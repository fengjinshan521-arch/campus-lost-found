"""本地开发入口：python run.py → http://127.0.0.1:5000"""
from dotenv import load_dotenv

load_dotenv()  # 必须在 create_app 之前加载 .env

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    print("校园失物招领平台后端启动：http://127.0.0.1:5000")
    print("数据库：", app.config["SQLALCHEMY_DATABASE_URI"].split("@")[-1])
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=True)
