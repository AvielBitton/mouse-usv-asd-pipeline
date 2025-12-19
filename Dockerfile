FROM python:3.8

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "ASD_Tool/asd_tool.py"]
