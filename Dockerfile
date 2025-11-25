FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .


RUN echo '#!/bin/bash\n\
\n\
echo "等待数据库启动..."\n\
sleep 10\n\
\n\
echo "初始化数据库..."\n\
python init_db.py\n\
\n\
echo "启动应用..."\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]