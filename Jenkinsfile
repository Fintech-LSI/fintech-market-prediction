pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-east-1'
        IMAGE_NAME = 'market-prediction'
        ECR_REGISTRY = 'public.ecr.aws/z1z0w2y6'
        EKS_CLUSTER_NAME = 'main-cluster'
        NAMESPACE = 'fintech'
    }
    
    stages {
        stage('Build Docker Image') {
            steps {
                script {
                    def imageLatest = "${ECR_REGISTRY}/${IMAGE_NAME}:latest"
                    sh """
                        docker build -t ${imageLatest} . --no-cache
                    """
                }
            }
        }
        
        stage('Push to ECR') {
            steps {
                script {
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: 'aws-credentials',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]]) {
                        sh "aws ecr-public get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}"
                        sh "docker push ${ECR_REGISTRY}/${IMAGE_NAME}:latest"
                    }
                }
            }
        }
        
        stage('Deploy to EKS') {
            steps {
                script {
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: 'aws-credentials',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]]) {
                        // Configure kubectl
                        sh "aws eks update-kubeconfig --region ${AWS_REGION} --name ${EKS_CLUSTER_NAME}"

                        // Create namespace if it doesn't exist
                        sh "kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -"
                        
                        sh """
                            kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                            kubectl apply -f k8s/deployment.yaml -n ${NAMESPACE}
                            kubectl apply -f k8s/service.yaml -n ${NAMESPACE}
                            kubectl apply -f k8s/ingress.yaml -n ${NAMESPACE}
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            sh "docker rmi ${ECR_REGISTRY}/${IMAGE_NAME}:latest || true"
            cleanWs()
        }
    }
}
