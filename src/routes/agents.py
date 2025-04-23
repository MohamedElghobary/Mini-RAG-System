from fastapi import APIRouter, Depends, Form, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController, AgentsController, NLPController
import aiofiles
from models import ResponseSignal
import logging
from models.ChunkModel import ChunkModel
from models.ProjectModel import ProjectModel
from models.AssetModel import AssetModel
from models.db_schemes import Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
from routes.schemes.nlp import SearchRequest
from helpers.jwt import get_current_user



logger = logging.getLogger('uvicorn.error')

agent_router = APIRouter(
    prefix="/api/v1/agent",
    tags=["api_v1", "agent"],
)

@agent_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings),
                      no_queries: int = Form(5)):                     # Allow keyword count
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": result_signal}
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error while uploading file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.FILE_UPLOAD_FAILED.value}
        )

    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )

    asset_resource = Asset(
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    
    # Extract queries using ProcessController
    try:
        process_controller = ProcessController(project_id=str(project.project_id))
        file_content = process_controller.get_file_content(file_id=file_id)
        
        
        if file_content:
            all_text = " ".join([doc.page_content for doc in file_content])
            queries = AgentsController.extract_search_queries_from_text(
                text=all_text,
                no_queries=no_queries,
            )

            agents_controller = AgentsController()  # create an instance
            web_results = await agents_controller.perform_web_search_for_queries(queries)


        else:
            logger.warning("No content extracted from file.")
            queries = []

    except Exception as e:
        logger.error(f"queries extraction failed: {e}")
        queries = []


    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": str(asset_record.asset_id),
            "queries": queries,                                 # Include extracted queries
            "web_search": web_results
        }
    )




@agent_router.post("/smart/search/{project_id}")
async def smart_search_with_fallback(request: Request, project_id: str, search_request: SearchRequest, current_user: dict = Depends(get_current_user)):

    user_id = current_user["user_id"]
    """
    Step 1: Try to answer from vector DB.
    Step 2: If similarity score is too low, extract queries from document and do web search.
    """

    # --- Prepare clients ---
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(
        project_id=project_id,
        user_id=user_id
        )

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
        project=project,
        query=search_request.text,
        limit=search_request.limit,
    )

    agents_controller = AgentsController()

    # --- Vector DB search ---
    results = await nlp_controller.search_vector_db_collection(
        project=project, text=search_request.text, limit=search_request.limit
    )

    if not results or len(results) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value}
        )

    # Sort by score just in case (if not already)
    results.sort(key=lambda r: getattr(r, "score", 0), reverse=True)
    top_result = results[0]
    threshold = 0.65

    if getattr(top_result, "score", 0) >= threshold:
        return JSONResponse(
            content={
                "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
                "source": "vector_db",
                "results": [r.dict() if hasattr(r, "dict") else r.__dict__ for r in results],
                "answer": answer
            }
        )


    # --- Vector score is too low → Web search using the question directly ---
    web_results_dict = await agents_controller.perform_web_search_for_queries([search_request.text])

    all_snippets = []
    for item in web_results_dict.get(search_request.text, []):
        snippet = item.get("content") or item.get("body") or item.get("snippet")
        if snippet:
            all_snippets.append(snippet)

    if not all_snippets:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.WEB_SEARCH_FAILED.value}
        )

    # --- Generate answer from web ---
    context = "\n".join(all_snippets[:10])  # Trim context
    prompt = f"""You are a helpful assistant. Based on the following web results, answer the question:

User's Question:
{search_request.text}

Web Search Results:
{context}

Answer:"""

    web_answer = request.app.generation_client.generate_text(prompt=prompt)

    return JSONResponse(
        content={
            "signal": ResponseSignal.WEB_SEARCH_USED.value,
            "source": "web",
            "question_used": search_request.text,
            "answer": web_answer,
            "web_results": web_results_dict
        }
    )