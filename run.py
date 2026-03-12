"""Entry point to run the AI Training Talent Platform."""
from ai_platform import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
