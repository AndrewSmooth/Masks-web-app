from fastapi import FastAPI, Request, Query, UploadFile, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path
from typing import Union, Annotated
from sqlalchemy import select
import aiofiles
import os
import glob
import json
import base64

from PIL import Image
import io
from CvMask import CvMask
import cv2

from schemas import AccessoryDTO, CategoryDTO, CategoryAddDTO, AccessoryAddDTO
from models import Accessory, Category
from database import get_session

app = FastAPI() 
# подключение обработчика статических файлов к основному приложению fastapi
# статические файлы (в папке ../static) будут доступны по пути: http://127.0.0.1:8000/static/images/cat.jpg
app.mount("/static", StaticFiles(directory="../static"), name="static")
templates = Jinja2Templates(directory='../templates')

@app.post("/accessories/add")
async def add_accessory(accessory: Annotated[AccessoryAddDTO, Query()], file: UploadFile):
    script_dir = os.path.dirname(os.path.dirname(__file__)) #<-- absolute dir the script is in
    rel_path = "static/images/accessories/"+file.filename
    abs_file_path = os.path.join(script_dir, rel_path)

    async with aiofiles.open(abs_file_path, 'wb') as out_file:    
        content = await file.read()  # async read   
        outContent = await out_file.write(content)  # async write 

    path = Path(abs_file_path)
    new_file_path = path.with_suffix(file.filename[-4:])
    path.rename(new_file_path)

    session = get_session()
    try:
        category = await session.execute(select(Category).where(Category.id==accessory.category_fk))
    except Exception as e:
        category = ''
        print("Exception", e)

    new_accessory = Accessory(name=accessory.name, image=rel_path[7:], category=category.scalar(), category_fk=accessory.category_fk)
    session.add(new_accessory)
    await session.commit()
    await session.close()

    return AccessoryDTO.model_validate(new_accessory, from_attributes=True)

@app.post("/categories/add")
async def add_category(category: Annotated[CategoryAddDTO, Query()], file: UploadFile):
    script_dir = os.path.dirname(os.path.dirname(__file__)) #<-- absolute dir the script is in
    rel_path = "static/images/categories/"+file.filename
    abs_file_path = os.path.join(script_dir, rel_path)

    async with aiofiles.open(abs_file_path, 'wb') as out_file:    
        content = await file.read()  # async read   
        outContent = await out_file.write(content)  # async write 

    path = Path(abs_file_path)
    new_file_path = path.with_suffix(file.filename[-4:])
    path.rename(new_file_path)

    new_category = Category(name=category.name, image=rel_path[7:])
    session = get_session()
    session.add(new_category)
    await session.commit()
    await session.close()

    return CategoryDTO.model_validate(new_category, from_attributes=True)

@app.get("/", response_class=HTMLResponse)
@app.get("/categories", response_class=HTMLResponse)
async def get_categories(request: Request):
    session = get_session()
    try:
        categories = await session.execute(select(Category))
    except Exception as e:
        categories = []
        print("EXCEPTION", e)
    finally:
        session.close()
    categories = categories.scalars().all() # scalars() - выводит список объектов без кортежей
    return templates.TemplateResponse(request=request, name="categories.html", context={"categories": categories})

@app.get("/categories/{category_id}", response_class=HTMLResponse)
async def get_accessories(request: Request, category_id: int):
    session = get_session()
    try:
        accessories = await session.execute(select(Accessory).where(Accessory.category_fk==category_id))
        category = await session.execute(select(Category).where(Category.id==category_id))
    except Exception as e:
        accessories = []
        print("EXCEPTION", e)
    finally:
        await session.close()
    accessories = accessories.scalars().all()

    return templates.TemplateResponse(request=request, name="accessories.html", context={"accessories": accessories, "category_name": category.scalar().name})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    script_dir = os.path.dirname(os.path.dirname(__file__)) #<-- absolute dir the script is in
    rel_session_dir_path = "static/sessions"
    full_path = os.path.join(script_dir, rel_session_dir_path)

    try:
        list_of_files = glob.glob(full_path+"/*") # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        directory_name = latest_file[::-1].split("/", 1)[0][::-1]
    except: 
        directory_name = "session1"
    # print("LAT FILE:", latest_file[::-1].split("/", 1)[0][::-1])

    # Create the directory
    try:
        rel_new_session_dir_path = rel_session_dir_path + "/" + directory_name
        abs_session_path = os.path.join(script_dir, rel_new_session_dir_path)
        os.mkdir(abs_session_path)
        print(f"Directory '{directory_name}' created successfully.")
    except FileExistsError:
        print(f"Directory '{directory_name}' already exists. Creating new")
        try:
            new_dir_name = directory_name[:-1]+str(int(directory_name[-1])+1)
            rel_new_session_dir_path = rel_session_dir_path + "/" + new_dir_name
            abs_session_path = os.path.join(script_dir, rel_new_session_dir_path)

            os.mkdir(abs_session_path)
            directory_name = new_dir_name
        except Exception as e:
            print(f"An error occurred: {e}")

    except PermissionError:
        print(f"Permission denied: Unable to create '{directory_name}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

    mask_path = os.path.join(script_dir, "static/images/masks/mask1.png")

    while True:
        response = await websocket.receive()

        if response:
            rel_path = "static/sessions/"+directory_name+"/"
            abs_file_path = os.path.join(script_dir, rel_path)
            print("REL", script_dir)
            print("ABS", abs_file_path)
            print("received") 
            print(response.keys())
            bytes = ""
            
            if response.get("bytes"):
                bytes = response.get("bytes")
            elif response.get("text"):
                mask_path = response.get("text").split("/", 3)[-1]
                mask_path = os.path.join(script_dir, mask_path)
                print("RECEIVED MASK PATH", mask_path)
            
            if bytes != "":
                print("MASK PATH", mask_path)
                # print(response.get("text").keys())
                # print(resp.get("text").keys())

                pre_img = io.BytesIO(bytes)
                received_image = Image.open(pre_img)
                received_image_path = abs_file_path+"/received-frame.png"
                received_image.save(received_image_path)

                new_image = cv2.imread(received_image_path, 1) 
                # rel_mask_path = "static/images/masks/mask1.png"
                class_mask_path = os.path.join(script_dir, mask_path)
                filter_name = class_mask_path[::-1].split("/", 1)[0][::-1][:-4]
                # print("MASK NAME:", class_mask_path[::-1].split("/", 1)[0][::-1][:-4])


                cv_mask = CvMask("/home/andrew/IT-projects-start/static/")
                processed_image_path = abs_file_path+"/processed-frame.png"
                cv_mask.process_frame(filter_name, new_image, processed_image_path)
                
                # cv2.imwrite(processed_image_path, processed_img)
                # processed_img = cv_mask.process_frame(class_mask_path, new_image, processed_image_path)
                # processed_image_path = abs_file_path+"/processed-frame.png"
                # cv2.imwrite(processed_image_path, processed_img)

                static_path = rel_path+"processed-frame.png"
                await websocket.send_text(static_path.split("/",1)[1])
                print("SENT")



            # image = cv2.imread(received_image_path)  # Замените на путь к вашему изображению
            # _, buffer = cv2.imencode('.jpg', image)  # Кодируем в формате JPEG
            # jpg_as_text = base64.b64encode(buffer).decode('utf-8')  # Кодируем в base64

            # with open(received_image_path, "rb") as image:
            #     f = image.read()
            #     b = bytearray(f)
            
            # data = json.dumps({"image": processed_img.encode('base64')})

            # data = json.loads(b.decode('base64'))

            # cv2.imshow("MASK IMAGE", processed_img)
            # cv2.waitKey(0)