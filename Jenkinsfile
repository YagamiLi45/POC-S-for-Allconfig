pipeline {
    agent any

    environment {
        VENV = "venv"
        PYTHON = "C:\\Users\\mtamb\\AppData\\Local\\Programs\\Python\\Python311\\python.exe"
    }

    stages {
        stage('Setup Python') {
            steps {
                bat """
                    %PYTHON% -m venv %VENV%
                    %VENV%\\Scripts\\python.exe -m pip install --upgrade pip
                    %VENV%\\Scripts\\python.exe -m pip install -r requirements.txt
                """
            }
        }

        stage('Run Application') {
            steps {
                withCredentials([
                    string(credentialsId: 'PINECONE_API_KEY', variable: 'PINECONE_API_KEY'),
                    string(credentialsId: 'GEMINI_API_KEY', variable: 'GEMINI_API_KEY')
                ]) {
                    echo "Running application with Pinecone + Gemini keys..."
                    bat """
                        set PINECONE_API_KEY=%PINECONE_API_KEY%
                        set GEMINI_API_KEY=%GEMINI_API_KEY%
                        set MODE=web
                        %VENV%\\Scripts\\streamlit run app.py --server.port 8501
                    """
                }
            }
        }
    }
}
