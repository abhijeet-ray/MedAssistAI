"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.MedAssistStack = void 0;
const cdk = __importStar(require("aws-cdk-lib"));
const s3 = __importStar(require("aws-cdk-lib/aws-s3"));
const dynamodb = __importStar(require("aws-cdk-lib/aws-dynamodb"));
const lambda = __importStar(require("aws-cdk-lib/aws-lambda"));
const apigateway = __importStar(require("aws-cdk-lib/aws-apigateway"));
const iam = __importStar(require("aws-cdk-lib/aws-iam"));
const events = __importStar(require("aws-cdk-lib/aws-events"));
const targets = __importStar(require("aws-cdk-lib/aws-events-targets"));
class MedAssistStack extends cdk.Stack {
    constructor(scope, id, props) {
        super(scope, id, props);
        // ========================================
        // S3 Buckets with AES-256 Encryption
        // ========================================
        const documentsBucket = new s3.Bucket(this, 'DocumentsBucket', {
            bucketName: `medassist-documents-${this.account}`,
            encryption: s3.BucketEncryption.S3_MANAGED, // AES-256
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
            versioned: false,
            lifecycleRules: [
                {
                    id: 'DeleteOldSessions',
                    expiration: cdk.Duration.days(1), // 24-hour cleanup
                    prefix: 'sessions/',
                },
            ],
            removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
            autoDeleteObjects: true, // For dev/test
        });
        const knowledgeBaseBucket = new s3.Bucket(this, 'KnowledgeBaseBucket', {
            bucketName: `medassist-knowledge-base-${this.account}`,
            encryption: s3.BucketEncryption.S3_MANAGED, // AES-256
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
            versioned: false,
            removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
            autoDeleteObjects: true, // For dev/test
        });
        // ========================================
        // DynamoDB Tables with Encryption
        // ========================================
        const sessionTable = new dynamodb.Table(this, 'SessionTable', {
            tableName: 'MedAssist-Sessions',
            partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
            sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption: dynamodb.TableEncryption.AWS_MANAGED,
            pointInTimeRecovery: true,
            removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
        });
        const documentTable = new dynamodb.Table(this, 'DocumentTable', {
            tableName: 'MedAssist-Documents',
            partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
            sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption: dynamodb.TableEncryption.AWS_MANAGED,
            pointInTimeRecovery: true,
            removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
        });
        const embeddingTable = new dynamodb.Table(this, 'EmbeddingTable', {
            tableName: 'MedAssist-Embeddings',
            partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
            sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption: dynamodb.TableEncryption.AWS_MANAGED,
            pointInTimeRecovery: true,
            removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
        });
        const chatHistoryTable = new dynamodb.Table(this, 'ChatHistoryTable', {
            tableName: 'MedAssist-ChatHistory',
            partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
            sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption: dynamodb.TableEncryption.AWS_MANAGED,
            timeToLiveAttribute: 'ttl', // 24-hour TTL
            pointInTimeRecovery: true,
            removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev/test
        });
        // ========================================
        // IAM Role for Lambda Functions (Least Privilege)
        // ========================================
        const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
            description: 'Execution role for MedAssist Lambda functions with least privilege',
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
            ],
        });
        // S3 permissions
        documentsBucket.grantReadWrite(lambdaRole);
        knowledgeBaseBucket.grantReadWrite(lambdaRole);
        // DynamoDB permissions
        sessionTable.grantReadWriteData(lambdaRole);
        documentTable.grantReadWriteData(lambdaRole);
        embeddingTable.grantReadWriteData(lambdaRole);
        chatHistoryTable.grantReadWriteData(lambdaRole);
        // AWS AI/ML service permissions
        lambdaRole.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
                'textract:DetectDocumentText',
                'textract:AnalyzeDocument',
            ],
            resources: ['*'],
        }));
        lambdaRole.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
                'rekognition:DetectText',
                'rekognition:DetectLabels',
            ],
            resources: ['*'],
        }));
        lambdaRole.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
                'comprehendmedical:DetectEntitiesV2',
                'comprehendmedical:InferICD10CM',
                'comprehendmedical:InferRxNorm',
            ],
            resources: ['*'],
        }));
        lambdaRole.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
                'bedrock:InvokeModel',
            ],
            resources: [
                `arn:aws:bedrock:${this.region}::foundation-model/*`,
            ],
        }));
        // Lambda invoke permission for UploadLambda to invoke ExtractionLambda
        lambdaRole.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: ['lambda:InvokeFunction'],
            resources: [`arn:aws:lambda:${this.region}:${this.account}:function:MedAssist-Extraction`],
        }));
        // ========================================
        // Lambda Functions
        // ========================================
        const uploadLambda = new lambda.Function(this, 'UploadLambda', {
            functionName: 'MedAssist-Upload',
            runtime: lambda.Runtime.PYTHON_3_11,
            handler: 'upload.handler',
            code: lambda.Code.fromAsset('../lambda/upload'),
            role: lambdaRole,
            timeout: cdk.Duration.seconds(30),
            memorySize: 512,
            environment: {
                DOCUMENTS_BUCKET: documentsBucket.bucketName,
                SESSION_TABLE: sessionTable.tableName,
                DOCUMENT_TABLE: documentTable.tableName,
                EXTRACTION_LAMBDA: 'MedAssist-Extraction',
            },
        });
        const extractionLambda = new lambda.Function(this, 'ExtractionLambda', {
            functionName: 'MedAssist-Extraction',
            runtime: lambda.Runtime.PYTHON_3_11,
            handler: 'extraction.handler',
            code: lambda.Code.fromAsset('../lambda/extraction'),
            role: lambdaRole,
            timeout: cdk.Duration.seconds(300), // 5 minutes for document processing
            memorySize: 1024,
            environment: {
                DOCUMENTS_BUCKET: documentsBucket.bucketName,
                DOCUMENT_TABLE: documentTable.tableName,
            },
        });
        const embeddingLambda = new lambda.Function(this, 'EmbeddingLambda', {
            functionName: 'MedAssist-Embedding',
            runtime: lambda.Runtime.PYTHON_3_11,
            handler: 'embedding.handler',
            code: lambda.Code.fromAsset('../lambda/embedding'),
            role: lambdaRole,
            timeout: cdk.Duration.seconds(300),
            memorySize: 2048,
            environment: {
                EMBEDDINGS_TABLE: embeddingTable.tableName,
                DOCUMENT_TABLE: documentTable.tableName,
                KNOWLEDGE_BASE_BUCKET: knowledgeBaseBucket.bucketName,
            },
        });
        const ragLambda = new lambda.Function(this, 'RAGLambda', {
            functionName: 'MedAssist-RAG',
            runtime: lambda.Runtime.PYTHON_3_11,
            handler: 'rag.handler',
            code: lambda.Code.fromAsset('../lambda/rag', {
                exclude: [
                    '*.zip',
                    '*_backup.py',
                    '*_previous.py',
                    '*_simplified.py',
                    '*_ultra_simple.py',
                    'test_*.py',
                    '__pycache__',
                    'lambda_build',
                    'package',
                    'simplified_build',
                    'ultra_simple_build',
                ],
            }),
            role: lambdaRole,
            timeout: cdk.Duration.seconds(90),
            memorySize: 2048,
            environment: {
                DOCUMENT_TABLE: documentTable.tableName,
                EMBEDDINGS_TABLE: embeddingTable.tableName,
                KNOWLEDGE_BASE_BUCKET: knowledgeBaseBucket.bucketName,
                CHAT_HISTORY_TABLE: chatHistoryTable.tableName,
            },
        });
        const dashboardLambda = new lambda.Function(this, 'DashboardLambda', {
            functionName: 'MedAssist-Dashboard',
            runtime: lambda.Runtime.PYTHON_3_11,
            handler: 'dashboard.handler',
            code: lambda.Code.fromAsset('../lambda/dashboard'),
            role: lambdaRole,
            timeout: cdk.Duration.seconds(30),
            memorySize: 1024,
            environment: {
                EMBEDDINGS_TABLE: embeddingTable.tableName,
                DOCUMENT_TABLE: documentTable.tableName,
            },
        });
        const exportLambda = new lambda.Function(this, 'ExportLambda', {
            functionName: 'MedAssist-Export',
            runtime: lambda.Runtime.PYTHON_3_11,
            handler: 'export.handler',
            code: lambda.Code.fromAsset('../lambda/export'),
            role: lambdaRole,
            timeout: cdk.Duration.seconds(60),
            memorySize: 1024,
            environment: {
                DOCUMENTS_BUCKET: documentsBucket.bucketName,
                SESSION_TABLE: sessionTable.tableName,
            },
        });
        const cleanupLambda = new lambda.Function(this, 'CleanupLambda', {
            functionName: 'MedAssist-Cleanup',
            runtime: lambda.Runtime.PYTHON_3_11,
            handler: 'cleanup.handler',
            code: lambda.Code.fromAsset('../lambda/cleanup'),
            role: lambdaRole,
            timeout: cdk.Duration.seconds(60),
            memorySize: 512,
            environment: {
                DOCUMENTS_BUCKET: documentsBucket.bucketName,
                SESSION_TABLE: sessionTable.tableName,
                DOCUMENT_TABLE: documentTable.tableName,
                EMBEDDING_TABLE: embeddingTable.tableName,
            },
        });
        // Update UploadLambda environment with ExtractionLambda ARN
        uploadLambda.addEnvironment('EXTRACTION_LAMBDA_ARN', extractionLambda.functionArn);
        // ========================================
        // EventBridge Rule for Session Cleanup (runs every 24 hours)
        // ========================================
        const cleanupRule = new events.Rule(this, 'SessionCleanupRule', {
            ruleName: 'MedAssist-SessionCleanup',
            description: 'Triggers session cleanup Lambda every 24 hours',
            schedule: events.Schedule.rate(cdk.Duration.hours(24)),
        });
        cleanupRule.addTarget(new targets.LambdaFunction(cleanupLambda));
        // ========================================
        // API Gateway with TLS 1.2+, CloudWatch Logging, and CORS
        // ========================================
        const api = new apigateway.RestApi(this, 'MedAssistAPI', {
            restApiName: 'MedAssist API',
            description: 'API for MedAssist AI System',
            deployOptions: {
                stageName: 'prod',
                loggingLevel: apigateway.MethodLoggingLevel.INFO,
                dataTraceEnabled: true,
                metricsEnabled: true,
            },
            defaultCorsPreflightOptions: {
                allowOrigins: ['*'],
                allowMethods: apigateway.Cors.ALL_METHODS,
                allowHeaders: ['*'],
                allowCredentials: false,
                statusCode: 200,
            },
            endpointConfiguration: {
                types: [apigateway.EndpointType.REGIONAL],
            },
            policy: new iam.PolicyDocument({
                statements: [
                    new iam.PolicyStatement({
                        effect: iam.Effect.ALLOW,
                        principals: [new iam.AnyPrincipal()],
                        actions: ['execute-api:Invoke'],
                        resources: ['execute-api:/*'],
                        conditions: {
                            StringEquals: {
                                'aws:SecureTransport': 'true', // Enforce TLS
                            },
                        },
                    }),
                ],
            }),
        });
        // API Endpoints with Lambda proxy integration (Lambda returns CORS headers)
        // CORS is handled by defaultCorsPreflightOptions at API level
        const uploadResource = api.root.addResource('upload');
        uploadResource.addMethod('POST', new apigateway.LambdaIntegration(uploadLambda, {
            proxy: true,
        }));
        const chatResource = api.root.addResource('chat');
        chatResource.addMethod('POST', new apigateway.LambdaIntegration(ragLambda, {
            proxy: true,
        }));
        const dashboardResource = api.root.addResource('dashboard');
        dashboardResource.addMethod('GET', new apigateway.LambdaIntegration(dashboardLambda, {
            proxy: true,
        }));
        const exportResource = api.root.addResource('export');
        exportResource.addMethod('POST', new apigateway.LambdaIntegration(exportLambda, {
            proxy: true,
        }));
        // ========================================
        // Outputs
        // ========================================
        new cdk.CfnOutput(this, 'APIEndpoint', {
            value: api.url,
            description: 'API Gateway endpoint URL',
            exportName: 'MedAssistAPIEndpoint',
        });
        new cdk.CfnOutput(this, 'DocumentsBucketName', {
            value: documentsBucket.bucketName,
            description: 'S3 bucket for documents',
            exportName: 'MedAssistDocumentsBucket',
        });
        new cdk.CfnOutput(this, 'SessionTableName', {
            value: sessionTable.tableName,
            description: 'DynamoDB table for sessions',
            exportName: 'MedAssistSessionTable',
        });
    }
}
exports.MedAssistStack = MedAssistStack;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoibWVkYXNzaXN0LXN0YWNrLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsibWVkYXNzaXN0LXN0YWNrLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQUFBLGlEQUFtQztBQUNuQyx1REFBeUM7QUFDekMsbUVBQXFEO0FBQ3JELCtEQUFpRDtBQUNqRCx1RUFBeUQ7QUFDekQseURBQTJDO0FBQzNDLCtEQUFpRDtBQUNqRCx3RUFBMEQ7QUFHMUQsTUFBYSxjQUFlLFNBQVEsR0FBRyxDQUFDLEtBQUs7SUFDM0MsWUFBWSxLQUFnQixFQUFFLEVBQVUsRUFBRSxLQUFzQjtRQUM5RCxLQUFLLENBQUMsS0FBSyxFQUFFLEVBQUUsRUFBRSxLQUFLLENBQUMsQ0FBQztRQUV4QiwyQ0FBMkM7UUFDM0MscUNBQXFDO1FBQ3JDLDJDQUEyQztRQUUzQyxNQUFNLGVBQWUsR0FBRyxJQUFJLEVBQUUsQ0FBQyxNQUFNLENBQUMsSUFBSSxFQUFFLGlCQUFpQixFQUFFO1lBQzdELFVBQVUsRUFBRSx1QkFBdUIsSUFBSSxDQUFDLE9BQU8sRUFBRTtZQUNqRCxVQUFVLEVBQUUsRUFBRSxDQUFDLGdCQUFnQixDQUFDLFVBQVUsRUFBRSxVQUFVO1lBQ3RELGlCQUFpQixFQUFFLEVBQUUsQ0FBQyxpQkFBaUIsQ0FBQyxTQUFTO1lBQ2pELFNBQVMsRUFBRSxLQUFLO1lBQ2hCLGNBQWMsRUFBRTtnQkFDZDtvQkFDRSxFQUFFLEVBQUUsbUJBQW1CO29CQUN2QixVQUFVLEVBQUUsR0FBRyxDQUFDLFFBQVEsQ0FBQyxJQUFJLENBQUMsQ0FBQyxDQUFDLEVBQUUsa0JBQWtCO29CQUNwRCxNQUFNLEVBQUUsV0FBVztpQkFDcEI7YUFDRjtZQUNELGFBQWEsRUFBRSxHQUFHLENBQUMsYUFBYSxDQUFDLE9BQU8sRUFBRSxlQUFlO1lBQ3pELGlCQUFpQixFQUFFLElBQUksRUFBRSxlQUFlO1NBQ3pDLENBQUMsQ0FBQztRQUVILE1B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LFlBQVksRUFBRTtZQUM5RSxLQUFLLEVBQUUsSUFBSTtTQUNaLENBQUMsQ0FBQyxDQUFDO1FBRUosMkNBQTJDO1FBQzNDLFVBQVU7UUFDViwyQ0FBMkM7UUFFM0MsSUFBSSxHQUFHLENBQUMsU0FBUyxDQUFDLElBQUksRUFBRSxhQUFhLEVBQUU7WUFDckMsS0FBSyxFQUFFLEdBQUcsQ0FBQyxHQUFHO1lBQ2QsV0FBVyxFQUFFLDBCQUEwQjtZQUN2QyxVQUFVLEVBQUUsc0JBQXNCO1NBQ25DLENBQUMsQ0FBQztRQUVILElBQUksR0FBRyxDQUFDLFNBQVMsQ0FBQyxJQUFJLEVBQUUscUJBQXFCLEVBQUU7WUFDN0MsS0FBSyxFQUFFLGVBQWUsQ0FBQyxVQUFVO1lBQ2pDLFdBQVcsRUFBRSx5QkFBeUI7WUFDdEMsVUFBVSxFQUFFLDBCQUEwQjtTQUN2QyxDQUFDLENBQUM7UUFFSCxJQUFJLEdBQUcsQ0FBQyxTQUFTLENBQUMsSUFBSSxFQUFFLGtCQUFrQixFQUFFO1lBQzFDLEtBQUssRUFBRSxZQUFZLENBQUMsU0FBUztZQUM3QixXQUFXLEVBQUUsNkJBQTZCO1lBQzFDLFVBQVUsRUFBRSx1QkFBdUI7U0FDcEMsQ0FBQyxDQUFDO0lBQ0wsQ0FBQztDQUNGO0FBaFhELHdDQWdYQyIsInNvdXJjZXNDb250ZW50IjpbImltcG9ydCAqIGFzIGNkayBmcm9tICdhd3MtY2RrLWxpYic7XHJcbmltcG9ydCAqIGFzIHMzIGZyb20gJ2F3cy1jZGstbGliL2F3cy1zMyc7XHJcbmltcG9ydCAqIGFzIGR5bmFtb2RiIGZyb20gJ2F3cy1jZGstbGliL2F3cy1keW5hbW9kYic7XHJcbmltcG9ydCAqIGFzIGxhbWJkYSBmcm9tICdhd3MtY2RrLWxpYi9hd3MtbGFtYmRhJztcclxuaW1wb3J0ICogYXMgYXBpZ2F0ZXdheSBmcm9tICdhd3MtY2RrLWxpYi9hd3MtYXBpZ2F0ZXdheSc7XHJcbmltcG9ydCAqIGFzIGlhbSBmcm9tICdhd3MtY2RrLWxpYi9hd3MtaWFtJztcclxuaW1wb3J0ICogYXMgZXZlbnRzIGZyb20gJ2F3cy1jZGstbGliL2F3cy1ldmVudHMnO1xyXG5pbXBvcnQgKiBhcyB0YXJnZXRzIGZyb20gJ2F3cy1jZGstbGliL2F3cy1ldmVudHMtdGFyZ2V0cyc7XHJcbmltcG9ydCB7IENvbnN0cnVjdCB9IGZyb20gJ2NvbnN0cnVjdHMnO1xyXG5cclxuZXhwb3J0IGNsYXNzIE1lZEFzc2lzdFN0YWNrIGV4dGVuZHMgY2RrLlN0YWNrIHtcclxuICBjb25zdHJ1Y3RvcihzY29wZTogQ29uc3RydWN0LCBpZDogc3RyaW5nLCBwcm9wcz86IGNkay5TdGFja1Byb3BzKSB7XHJcbiAgICBzdXBlcihzY29wZSwgaWQsIHByb3BzKTtcclxuXHJcbiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XHJcbiAgICAvLyBTMyBCdWNrZXRzIHdpdGggQUVTLTI1NiBFbmNyeXB0aW9uXHJcbiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XHJcbiAgICBcclxuICAgIGNvbnN0IGRvY3VtZW50c0J1Y2tldCA9IG5ldyBzMy5CdWNrZXQodGhpcywgJ0RvY3VtZW50c0J1Y2tldCcsIHtcclxuICAgICAgYnVja2V0TmFtZTogYG1lZGFzc2lzdC1kb2N1bWVudHMtJHt0aGlzLmFjY291bnR9YCxcclxuICAgICAgZW5jcnlwdGlvbjogczMuQnVja2V0RW5jcnlwdGlvbi5TM19NQU5BR0VELCAvLyBBRVMtMjU2XHJcbiAgICAgIGJsb2NrUHVibGljQWNjZXNzOiBzMy5CbG9ja1B1YmxpY0FjY2Vzcy5CTE9DS19BTEwsXHJcbiAgICAgIHZlcnNpb25lZDogZmFsc2UsXHJcbiAgICAgIGxpZmVjeWNsZVJ1bGVzOiBbXHJcbiAgICAgICAge1xyXG4gICAgICAgICAgaWQ6ICdEZWxldGVPbGRTZXNzaW9ucycsXHJcbiAgICAgICAgICBleHBpcmF0aW9uOiBjZGsuRHVyYXRpb24uZGF5cygxKSwgLy8gMjQtaG91ciBjbGVhbnVwXHJcbiAgICAgICAgICBwcmVmaXg6ICdzZXNzaW9ucy8nLFxyXG4gICAgICAgIH0sXHJcbiAgICAgIF0sXHJcbiAgICAgIHJlbW92YWxQb2xpY3k6IGNkay5SZW1vdmFsUG9saWN5LkRFU1RST1ksIC8vIEZvciBkZXYvdGVzdFxyXG4gICAgICBhdXRvRGVsZXRlT2JqZWN0czogdHJ1ZSwgLy8gRm9yIGRldi90ZXN0XHJcbiAgICB9KTtcclxuXHJcbiAgICBjb25zdCBrbm93bGVkZ2VCYXNlQnVja2V0ID0gbmV3IHMzLkJ1Y2tldCh0aGlzLCAnS25vd2xlZGdlQmFzZUJ1Y2tldCcsIHtcclxuICAgICAgYnVja2V0TmFtZTogYG1lZGFzc2lzdC1rbm93bGVkZ2UtYmFzZS0ke3RoaXMuYWNjb3VudH1gLFxyXG4gICAgICBlbmNyeXB0aW9uOiBzMy5CdWNrZXRFbmNyeXB0aW9uLlMzX01BTkFHRUQsIC8vIEFFUy0yNTZcclxuICAgICAgYmxvY2tQdWJsaWNBY2Nlc3M6IHMzLkJsb2NrUHVibGljQWNjZXNzLkJMT0NLX0FMTCxcclxuICAgICAgdmVyc2lvbmVkOiBmYWxzZSxcclxuICAgICAgcmVtb3ZhbFBvbGljeTogY2RrLlJlbW92YWxQb2xpY3kuREVTVFJPWSwgLy8gRm9yIGRldi90ZXN0XHJcbiAgICAgIGF1dG9EZWxldGVPYmplY3RzOiB0cnVlLCAvLyBGb3IgZGV2L3Rlc3RcclxuICAgIH0pO1xyXG5cclxuICAgIC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cclxuICAgIC8vIER5bmFtb0RCIFRhYmxlcyB3aXRoIEVuY3J5cHRpb25cclxuICAgIC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cclxuICAgIFxyXG4gICAgY29uc3Qgc2Vzc2lvblRhYmxlID0gbmV3IGR5bmFtb2RiLlRhYmxlKHRoaXMsICdTZXNzaW9uVGFibGUnLCB7XHJcbiAgICAgIHRhYmxlTmFtZTogJ01lZEFzc2lzdC1TZXNzaW9ucycsXHJcbiAgICAgIHBhcnRpdGlvbktleTogeyBuYW1lOiAnUEsnLCB0eXBlOiBkeW5hbW9kYi5BdHRyaWJ1dGVUeXBlLlNUUklORyB9LFxyXG4gICAgICBzb3J0S2V5OiB7IG5hbWU6ICdTSycsIHR5cGU6IGR5bmFtb2RiLkF0dHJpYnV0ZVR5cGUuU1RSSU5HIH0sXHJcbiAgICAgIGJpbGxpbmdNb2RlOiBkeW5hbW9kYi5CaWxsaW5nTW9kZS5QQVlfUEVSX1JFUVVFU1QsXHJcbiAgICAgIGVuY3J5cHRpb246IGR5bmFtb2RiLlRhYmxlRW5jcnlwdGlvbi5BV1NfTUFOQUdFRCxcclxuICAgICAgcG9pbnRJblRpbWVSZWNvdmVyeTogdHJ1ZSxcclxuICAgICAgcmVtb3ZhbFBvbGljeTogY2RrLlJlbW92YWxQb2xpY3kuREVTVFJPWSwgLy8gRm9yIGRldi90ZXN0XHJcbiAgICB9KTtcclxuXHJcbiAgICBjb25zdCBkb2N1bWVudFRhYmxlID0gbmV3IGR5bmFtb2RiLlRhYmxlKHRoaXMsICdEb2N1bWVudFRhYmxlJywge1xyXG4gICAgICB0YWJsZU5hbWU6ICdNZWRBc3Npc3QtRG9jdW1lbnRzJyxcclxuICAgICAgcGFydGl0aW9uS2V5OiB7IG5hbWU6ICdQSycsIHR5cGU6IGR5bmFtb2RiLkF0dHJpYnV0ZVR5cGUuU1RSSU5HIH0sXHJcbiAgICAgIHNvcnRLZXk6IHsgbmFtZTogJ1NLJywgdHlwZTogZHluYW1vZGIuQXR0cmlidXRlVHlwZS5TVFJJTkcgfSxcclxuICAgICAgYmlsbGluZ01vZGU6IGR5bmFtb2RiLkJpbGxpbmdNb2RlLlBBWV9QRVJfUkVRVUVTVCxcclxuICAgICAgZW5jcnlwdGlvbjogZHluYW1vZGIuVGFibGVFbmNyeXB0aW9uLkFXU19NQU5BR0VELFxyXG4gICAgICBwb2ludEluVGltZVJlY292ZXJ5OiB0cnVlLFxyXG4gICAgICByZW1vdmFsUG9saWN5OiBjZGsuUmVtb3ZhbFBvbGljeS5ERVNUUk9ZLCAvLyBGb3IgZGV2L3Rlc3RcclxuICAgIH0pO1xyXG5cclxuICAgIGNvbnN0IGVtYmVkZGluZ1RhYmxlID0gbmV3IGR5bmFtb2RiLlRhYmxlKHRoaXMsICdFbWJlZGRpbmdUYWJsZScsIHtcclxuICAgICAgdGFibGVOYW1lOiAnTWVkQXNzaXN0LUVtYmVkZGluZ3MnLFxyXG4gICAgICBwYXJ0aXRpb25LZXk6IHsgbmFtZTogJ1BLJywgdHlwZTogZHluYW1vZGIuQXR0cmlidXRlVHlwZS5TVFJJTkcgfSxcclxuICAgICAgc29ydEtleTogeyBuYW1lOiAnU0snLCB0eXBlOiBkeW5hbW9kYi5BdHRyaWJ1dGVUeXBlLlNUUklORyB9LFxyXG4gICAgICBiaWxsaW5nTW9kZTogZHluYW1vZGIuQmlsbGluZ01vZGUuUEFZX1BFUl9SRVFVRVNULFxyXG4gICAgICBlbmNyeXB0aW9uOiBkeW5hbW9kYi5UYWJsZUVuY3J5cHRpb24uQVdTX01BTkFHRUQsXHJcbiAgICAgIHBvaW50SW5UaW1lUmVjb3Zlcnk6IHRydWUsXHJcbiAgICAgIHJlbW92YWxQb2xpY3k6IGNkay5SZW1vdmFsUG9saWN5LkRFU1RST1ksIC8vIEZvciBkZXYvdGVzdFxyXG4gICAgfSk7XHJcblxyXG4gICAgY29uc3QgY2hhdEhpc3RvcnlUYWJsZSA9IG5ldyBkeW5hbW9kYi5UYWJsZSh0aGlzLCAnQ2hhdEhpc3RvcnlUYWJsZScsIHtcclxuICAgICAgdGFibGVOYW1lOiAnTWVkQXNzaXN0LUNoYXRIaXN0b3J5JyxcclxuICAgICAgcGFydGl0aW9uS2V5OiB7IG5hbWU6ICdQSycsIHR5cGU6IGR5bmFtb2RiLkF0dHJpYnV0ZVR5cGUuU1RSSU5HIH0sXHJcbiAgICAgIHNvcnRLZXk6IHsgbmFtZTogJ1NLJywgdHlwZTogZHluYW1vZGIuQXR0cmlidXRlVHlwZS5TVFJJTkcgfSxcclxuICAgICAgYmlsbGluZ01vZGU6IGR5bmFtb2RiLkJpbGxpbmdNb2RlLlBBWV9QRVJfUkVRVUVTVCxcclxuICAgICAgZW5jcnlwdGlvbjogZHluYW1vZGIuVGFibGVFbmNyeXB0aW9uLkFXU19NQU5BR0VELFxyXG4gICAgICB0aW1lVG9MaXZlQXR0cmlidXRlOiAndHRsJywgLy8gMjQtaG91ciBUVExcclxuICAgICAgcG9pbnRJblRpbWVSZWNvdmVyeTogdHJ1ZSxcclxuICAgICAgcmVtb3ZhbFBvbGljeTogY2RrLlJlbW92YWxQb2xpY3kuREVTVFJPWSwgLy8gRm9yIGRldi90ZXN0XHJcbiAgICB9KTtcclxuXHJcbiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XHJcbiAgICAvLyBJQU0gUm9sZSBmb3IgTGFtYmRhIEZ1bmN0aW9ucyAoTGVhc3QgUHJpdmlsZWdlKVxyXG4gICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxyXG4gICAgXHJcbiAgICBjb25zdCBsYW1iZGFSb2xlID0gbmV3IGlhbS5Sb2xlKHRoaXMsICdMYW1iZGFFeGVjdXRpb25Sb2xlJywge1xyXG4gICAgICBhc3N1bWVkQnk6IG5ldyBpYW0uU2VydmljZVByaW5jaXBhbCgnbGFtYmRhLmFtYXpvbmF3cy5jb20nKSxcclxuICAgICAgZGVzY3JpcHRpb246ICdFeGVjdXRpb24gcm9sZSBmb3IgTWVkQXNzaXN0IExhbWJkYSBmdW5jdGlvbnMgd2l0aCBsZWFzdCBwcml2aWxlZ2UnLFxyXG4gICAgICBtYW5hZ2VkUG9saWNpZXM6IFtcclxuICAgICAgICBpYW0uTWFuYWdlZFBvbGljeS5mcm9tQXdzTWFuYWdlZFBvbGljeU5hbWUoJ3NlcnZpY2Utcm9sZS9BV1NMYW1iZGFCYXNpY0V4ZWN1dGlvblJvbGUnKSxcclxuICAgICAgXSxcclxuICAgIH0pO1xyXG5cclxuICAgIC8vIFMzIHBlcm1pc3Npb25zXHJcbiAgICBkb2N1bWVudHNCdWNrZXQuZ3JhbnRSZWFkV3JpdGUobGFtYmRhUm9sZSk7XHJcbiAgICBrbm93bGVkZ2VCYXNlQnVja2V0LmdyYW50UmVhZFdyaXRlKGxhbWJkYVJvbGUpO1xyXG5cclxuICAgIC8vIER5bmFtb0RCIHBlcm1pc3Npb25zXHJcbiAgICBzZXNzaW9uVGFibGUuZ3JhbnRSZWFkV3JpdGVEYXRhKGxhbWJkYVJvbGUpO1xyXG4gICAgZG9jdW1lbnRUYWJsZS5ncmFudFJlYWRXcml0ZURhdGEobGFtYmRhUm9sZSk7XHJcbiAgICBlbWJlZGRpbmdUYWJsZS5ncmFudFJlYWRXcml0ZURhdGEobGFtYmRhUm9sZSk7XHJcbiAgICBjaGF0SGlzdG9yeVRhYmxlLmdyYW50UmVhZFdyaXRlRGF0YShsYW1iZGFSb2xlKTtcclxuXHJcbiAgICAvLyBBV1MgQUkvTUwgc2VydmljZSBwZXJtaXNzaW9uc1xyXG4gICAgbGFtYmRhUm9sZS5hZGRUb1BvbGljeShuZXcgaWFtLlBvbGljeVN0YXRlbWVudCh7XHJcbiAgICAgIGVmZmVjdDogaWFtLkVmZmVjdC5BTExPVyxcclxuICAgICAgYWN0aW9uczogW1xyXG4gICAgICAgICd0ZXh0cmFjdDpEZXRlY3REb2N1bWVudFRleHQnLFxyXG4gICAgICAgICd0ZXh0cmFjdDpBbmFseXplRG9jdW1lbnQnLFxyXG4gICAgICBdLFxyXG4gICAgICByZXNvdXJjZXM6IFsnKiddLFxyXG4gICAgfSkpO1xyXG5cclxuICAgIGxhbWJkYVJvbGUuYWRkVG9Qb2xpY3kobmV3IGlhbS5Qb2xpY3lTdGF0ZW1lbnQoe1xyXG4gICAgICBlZmZlY3Q6IGlhbS5FZmZlY3QuQUxMT1csXHJcbiAgICAgIGFjdGlvbnM6IFtcclxuICAgICAgICAncmVrb2duaXRpb246RGV0ZWN0VGV4dCcsXHJcbiAgICAgICAgJ3Jla29nbml0aW9uOkRldGVjdExhYmVscycsXHJcbiAgICAgIF0sXHJcbiAgICAgIHJlc291cmNlczogWycqJ10sXHJcbiAgICB9KSk7XHJcblxyXG4gICAgbGFtYmRhUm9sZS5hZGRUb1BvbGljeShuZXcgaWFtLlBvbGljeVN0YXRlbWVudCh7XHJcbiAgICAgIGVmZmVjdDogaWFtLkVmZmVjdC5BTExPVyxcclxuICAgICAgYWN0aW9uczogW1xyXG4gICAgICAgICdjb21wcmVoZW5kbWVkaWNhbDpEZXRlY3RFbnRpdGllc1YyJyxcclxuICAgICAgICAnY29tcHJlaGVuZG1lZGljYWw6SW5mZXJJQ0QxMENNJyxcclxuICAgICAgICAnY29tcHJlaGVuZG1lZGljYWw6SW5mZXJSeE5vcm0nLFxyXG4gICAgICBdLFxyXG4gICAgICByZXNvdXJjZXM6IFsnKiddLFxyXG4gICAgfSkpO1xyXG5cclxuICAgIGxhbWJkYVJvbGUuYWRkVG9Qb2xpY3kobmV3IGlhbS5Qb2xpY3lTdGF0ZW1lbnQoe1xyXG4gICAgICBlZmZlY3Q6IGlhbS5FZmZlY3QuQUxMT1csXHJcbiAgICAgIGFjdGlvbnM6IFtcclxuICAgICAgICAnYmVkcm9jazpJbnZva2VNb2RlbCcsXHJcbiAgICAgIF0sXHJcbiAgICAgIHJlc291cmNlczogW1xyXG4gICAgICAgIGBhcm46YXdzOmJlZHJvY2s6JHt0aGlzLnJlZ2lvbn06OmZvdW5kYXRpb24tbW9kZWwvKmAsXHJcbiAgICAgIF0sXHJcbiAgICB9KSk7XHJcblxyXG4gICAgLy8gTGFtYmRhIGludm9rZSBwZXJtaXNzaW9uIGZvciBVcGxvYWRMYW1iZGEgdG8gaW52b2tlIEV4dHJhY3Rpb25MYW1iZGFcclxuICAgIGxhbWJkYVJvbGUuYWRkVG9Qb2xpY3kobmV3IGlhbS5Qb2xpY3lTdGF0ZW1lbnQoe1xyXG4gICAgICBlZmZlY3Q6IGlhbS5FZmZlY3QuQUxMT1csXHJcbiAgICAgIGFjdGlvbnM6IFsnbGFtYmRhOkludm9rZUZ1bmN0aW9uJ10sXHJcbiAgICAgIHJlc291cmNlczogW2Bhcm46YXdzOmxhbWJkYToke3RoaXMucmVnaW9ufToke3RoaXMuYWNjb3VudH06ZnVuY3Rpb246TWVkQXNzaXN0LUV4dHJhY3Rpb25gXSxcclxuICAgIH0pKTtcclxuXHJcbiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XHJcbiAgICAvLyBMYW1iZGEgRnVuY3Rpb25zXHJcbiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XHJcbiAgICBcclxuICAgIGNvbnN0IHVwbG9hZExhbWJkYSA9IG5ldyBsYW1iZGEuRnVuY3Rpb24odGhpcywgJ1VwbG9hZExhbWJkYScsIHtcclxuICAgICAgZnVuY3Rpb25OYW1lOiAnTWVkQXNzaXN0LVVwbG9hZCcsXHJcbiAgICAgIHJ1bnRpbWU6IGxhbWJkYS5SdW50aW1lLlBZVEhPTl8zXzExLFxyXG4gICAgICBoYW5kbGVyOiAndXBsb2FkLmhhbmRsZXInLFxyXG4gICAgICBjb2RlOiBsYW1iZGEuQ29kZS5mcm9tQXNzZXQoJy4uL2xhbWJkYS91cGxvYWQnKSxcclxuICAgICAgcm9sZTogbGFtYmRhUm9sZSxcclxuICAgICAgdGltZW91dDogY2RrLkR1cmF0aW9uLnNlY29uZHMoMzApLFxyXG4gICAgICBtZW1vcnlTaXplOiA1MTIsXHJcbiAgICAgIGVudmlyb25tZW50OiB7XHJcbiAgICAgICAgRE9DVU1FTlRTX0JVQ0tFVDogZG9jdW1lbnRzQnVja2V0LmJ1Y2tldE5hbWUsXHJcbiAgICAgICAgU0VTU0lPTl9UQUJMRTogc2Vzc2lvblRhYmxlLnRhYmxlTmFtZSxcclxuICAgICAgICBET0NVTUVOVF9UQUJMRTogZG9jdW1lbnRUYWJsZS50YWJsZU5hbWUsXHJcbiAgICAgICAgRVhUUkFDVElPTl9MQU1CREE6ICdNZWRBc3Npc3QtRXh0cmFjdGlvbicsXHJcbiAgICAgIH0sXHJcbiAgICB9KTtcclxuXHJcbiAgICBjb25zdCBleHRyYWN0aW9uTGFtYmRhID0gbmV3IGxhbWJkYS5GdW5jdGlvbih0aGlzLCAnRXh0cmFjdGlvbkxhbWJkYScsIHtcclxuICAgICAgZnVuY3Rpb25OYW1lOiAnTWVkQXNzaXN0LUV4dHJhY3Rpb24nLFxyXG4gICAgICBydW50aW1lOiBsYW1iZGEuUnVudGltZS5QWVRIT05fM18xMSxcclxuICAgICAgaGFuZGxlcjogJ2V4dHJhY3Rpb24uaGFuZGxlcicsXHJcbiAgICAgIGNvZGU6IGxhbWJkYS5Db2RlLmZyb21Bc3NldCgnLi4vbGFtYmRhL2V4dHJhY3Rpb24nKSxcclxuICAgICAgcm9sZTogbGFtYmRhUm9sZSxcclxuICAgICAgdGltZW91dDogY2RrLkR1cmF0aW9uLnNlY29uZHMoMzAwKSwgLy8gNSBtaW51dGVzIGZvciBkb2N1bWVudCBwcm9jZXNzaW5nXHJcbiAgICAgIG1lbW9yeVNpemU6IDEwMjQsXHJcbiAgICAgIGVudmlyb25tZW50OiB7XHJcbiAgICAgICAgRE9DVU1FTlRTX0JVQ0tFVDogZG9jdW1lbnRzQnVja2V0LmJ1Y2tldE5hbWUsXHJcbiAgICAgICAgRE9DVU1FTlRfVEFCTEU6IGRvY3VtZW50VGFibGUudGFibGVOYW1lLFxyXG4gICAgICB9LFxyXG4gICAgfSk7XHJcblxyXG4gICAgY29uc3QgZW1iZWRkaW5nTGFtYmRhID0gbmV3IGxhbWJkYS5GdW5jdGlvbih0aGlzLCAnRW1iZWRkaW5nTGFtYmRhJywge1xyXG4gICAgICBmdW5jdGlvbk5hbWU6ICdNZWRBc3Npc3QtRW1iZWRkaW5nJyxcclxuICAgICAgcnVudGltZTogbGFtYmRhLlJ1bnRpbWUuUFlUSE9OXzNfMTEsXHJcbiAgICAgIGhhbmRsZXI6ICdlbWJlZGRpbmcuaGFuZGxlcicsXHJcbiAgICAgIGNvZGU6IGxhbWJkYS5Db2RlLmZyb21Bc3NldCgnLi4vbGFtYmRhL2VtYmVkZGluZycpLFxyXG4gICAgICByb2xlOiBsYW1iZGFSb2xlLFxyXG4gICAgICB0aW1lb3V0OiBjZGsuRHVyYXRpb24uc2Vjb25kcygzMDApLFxyXG4gICAgICBtZW1vcnlTaXplOiAyMDQ4LFxyXG4gICAgICBlbnZpcm9ubWVudDoge1xyXG4gICAgICAgIEVNQkVERElOR1NfVEFCTEU6IGVtYmVkZGluZ1RhYmxlLnRhYmxlTmFtZSxcclxuICAgICAgICBET0NVTUVOVF9UQUJMRTogZG9jdW1lbnRUYWJsZS50YWJsZU5hbWUsXHJcbiAgICAgICAgS05PV0xFREdFX0JBU0VfQlVDS0VUOiBrbm93bGVkZ2VCYXNlQnVja2V0LmJ1Y2tldE5hbWUsXHJcbiAgICAgIH0sXHJcbiAgICB9KTtcclxuXHJcbiAgICBjb25zdCByYWdMYW1iZGEgPSBuZXcgbGFtYmRhLkZ1bmN0aW9uKHRoaXMsICdSQUdMYW1iZGEnLCB7XHJcbiAgICAgIGZ1bmN0aW9uTmFtZTogJ01lZEFzc2lzdC1SQUcnLFxyXG4gICAgICBydW50aW1lOiBsYW1iZGEuUnVudGltZS5QWVRIT05fM18xMSxcclxuICAgICAgaGFuZGxlcjogJ3JhZy5oYW5kbGVyJyxcclxuICAgICAgY29kZTogbGFtYmRhLkNvZGUuZnJvbUFzc2V0KCcuLi9sYW1iZGEvcmFnJywge1xyXG4gICAgICAgIGV4Y2x1ZGU6IFtcclxuICAgICAgICAgICcqLnppcCcsXHJcbiAgICAgICAgICAnKl9iYWNrdXAucHknLFxyXG4gICAgICAgICAgJypfcHJldmlvdXMucHknLFxyXG4gICAgICAgICAgJypfc2ltcGxpZmllZC5weScsXHJcbiAgICAgICAgICAnKl91bHRyYV9zaW1wbGUucHknLFxyXG4gICAgICAgICAgJ3Rlc3RfKi5weScsXHJcbiAgICAgICAgICAnX19weWNhY2hlX18nLFxyXG4gICAgICAgICAgJ2xhbWJkYV9idWlsZCcsXHJcbiAgICAgICAgICAncGFja2FnZScsXHJcbiAgICAgICAgICAnc2ltcGxpZmllZF9idWlsZCcsXHJcbiAgICAgICAgICAndWx0cmFfc2ltcGxlX2J1aWxkJyxcclxuICAgICAgICBdLFxyXG4gICAgICB9KSxcclxuICAgICAgcm9sZTogbGFtYmRhUm9sZSxcclxuICAgICAgdGltZW91dDogY2RrLkR1cmF0aW9uLnNlY29uZHMoOTApLFxyXG4gICAgICBtZW1vcnlTaXplOiAyMDQ4LFxyXG4gICAgICBlbnZpcm9ubWVudDoge1xyXG4gICAgICAgIERPQ1VNRU5UX1RBQkxFOiBkb2N1bWVudFRhYmxlLnRhYmxlTmFtZSxcclxuICAgICAgICBFTUJFRERJTkdTX1RBQkxFOiBlbWJlZGRpbmdUYWJsZS50YWJsZU5hbWUsXHJcbiAgICAgICAgS05PV0xFREdFX0JBU0VfQlVDS0VUOiBrbm93bGVkZ2VCYXNlQnVja2V0LmJ1Y2tldE5hbWUsXHJcbiAgICAgICAgQ0hBVF9ISVNUT1JZX1RBQkxFOiBjaGF0SGlzdG9yeVRhYmxlLnRhYmxlTmFtZSxcclxuICAgICAgfSxcclxuICAgIH0pO1xyXG5cclxuICAgIGNvbnN0IGRhc2hib2FyZExhbWJkYSA9IG5ldyBsYW1iZGEuRnVuY3Rpb24odGhpcywgJ0Rhc2hib2FyZExhbWJkYScsIHtcclxuICAgICAgZnVuY3Rpb25OYW1lOiAnTWVkQXNzaXN0LURhc2hib2FyZCcsXHJcbiAgICAgIHJ1bnRpbWU6IGxhbWJkYS5SdW50aW1lLlBZVEhPTl8zXzExLFxyXG4gICAgICBoYW5kbGVyOiAnZGFzaGJvYXJkLmhhbmRsZXInLFxyXG4gICAgICBjb2RlOiBsYW1iZGEuQ29kZS5mcm9tQXNzZXQoJy4uL2xhbWJkYS9kYXNoYm9hcmQnKSxcclxuICAgICAgcm9sZTogbGFtYmRhUm9sZSxcclxuICAgICAgdGltZW91dDogY2RrLkR1cmF0aW9uLnNlY29uZHMoMzApLFxyXG4gICAgICBtZW1vcnlTaXplOiAxMDI0LFxyXG4gICAgICBlbnZpcm9ubWVudDoge1xyXG4gICAgICAgIEVNQkVERElOR1NfVEFCTEU6IGVtYmVkZGluZ1RhYmxlLnRhYmxlTmFtZSxcclxuICAgICAgICBET0NVTUVOVF9UQUJMRTogZG9jdW1lbnRUYWJsZS50YWJsZU5hbWUsXHJcbiAgICAgIH0sXHJcbiAgICB9KTtcclxuXHJcbiAgICBjb25zdCBleHBvcnRMYW1iZGEgPSBuZXcgbGFtYmRhLkZ1bmN0aW9uKHRoaXMsICdFeHBvcnRMYW1iZGEnLCB7XHJcbiAgICAgIGZ1bmN0aW9uTmFtZTogJ01lZEFzc2lzdC1FeHBvcnQnLFxyXG4gICAgICBydW50aW1lOiBsYW1iZGEuUnVudGltZS5QWVRIT05fM18xMSxcclxuICAgICAgaGFuZGxlcjogJ2V4cG9ydC5oYW5kbGVyJyxcclxuICAgICAgY29kZTogbGFtYmRhLkNvZGUuZnJvbUFzc2V0KCcuLi9sYW1iZGEvZXhwb3J0JyksXHJcbiAgICAgIHJvbGU6IGxhbWJkYVJvbGUsXHJcbiAgICAgIHRpbWVvdXQ6IGNkay5EdXJhdGlvbi5zZWNvbmRzKDYwKSxcclxuICAgICAgbWVtb3J5U2l6ZTogMTAyNCxcclxuICAgICAgZW52aXJvbm1lbnQ6IHtcclxuICAgICAgICBET0NVTUVOVFNfQlVDS0VUOiBkb2N1bWVudHNCdWNrZXQuYnVja2V0TmFtZSxcclxuICAgICAgICBTRVNTSU9OX1RBQkxFOiBzZXNzaW9uVGFibGUudGFibGVOYW1lLFxyXG4gICAgICB9LFxyXG4gICAgfSk7XHJcblxyXG4gICAgY29uc3QgY2xlYW51cExhbWJkYSA9IG5ldyBsYW1iZGEuRnVuY3Rpb24odGhpcywgJ0NsZWFudXBMYW1iZGEnLCB7XHJcbiAgICAgIGZ1bmN0aW9uTmFtZTogJ01lZEFzc2lzdC1DbGVhbnVwJyxcclxuICAgICAgcnVudGltZTogbGFtYmRhLlJ1bnRpbWUuUFlUSE9OXzNfMTEsXHJcbiAgICAgIGhhbmRsZXI6ICdjbGVhbnVwLmhhbmRsZXInLFxyXG4gICAgICBjb2RlOiBsYW1iZGEuQ29kZS5mcm9tQXNzZXQoJy4uL2xhbWJkYS9jbGVhbnVwJyksXHJcbiAgICAgIHJvbGU6IGxhbWJkYVJvbGUsXHJcbiAgICAgIHRpbWVvdXQ6IGNkay5EdXJhdGlvbi5zZWNvbmRzKDYwKSxcclxuICAgICAgbWVtb3J5U2l6ZTogNTEyLFxyXG4gICAgICBlbnZpcm9ubWVudDoge1xyXG4gICAgICAgIERPQ1VNRU5UU19CVUNLRVQ6IGRvY3VtZW50c0J1Y2tldC5idWNrZXROYW1lLFxyXG4gICAgICAgIFNFU1NJT05fVEFCTEU6IHNlc3Npb25UYWJsZS50YWJsZU5hbWUsXHJcbiAgICAgICAgRE9DVU1FTlRfVEFCTEU6IGRvY3VtZW50VGFibGUudGFibGVOYW1lLFxyXG4gICAgICAgIEVNQkVERElOR19UQUJMRTogZW1iZWRkaW5nVGFibGUudGFibGVOYW1lLFxyXG4gICAgICB9LFxyXG4gICAgfSk7XHJcblxyXG4gICAgLy8gVXBkYXRlIFVwbG9hZExhbWJkYSBlbnZpcm9ubWVudCB3aXRoIEV4dHJhY3Rpb25MYW1iZGEgQVJOXHJcbiAgICB1cGxvYWRMYW1iZGEuYWRkRW52aXJvbm1lbnQoJ0VYVFJBQ1RJT05fTEFNQkRBX0FSTicsIGV4dHJhY3Rpb25MYW1iZGEuZnVuY3Rpb25Bcm4pO1xyXG5cclxuICAgIC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cclxuICAgIC8vIEV2ZW50QnJpZGdlIFJ1bGUgZm9yIFNlc3Npb24gQ2xlYW51cCAocnVucyBldmVyeSAyNCBob3VycylcclxuICAgIC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cclxuICAgIFxyXG4gICAgY29uc3QgY2xlYW51cFJ1bGUgPSBuZXcgZXZlbnRzLlJ1bGUodGhpcywgJ1Nlc3Npb25DbGVhbnVwUnVsZScsIHtcclxuICAgICAgcnVsZU5hbWU6ICdNZWRBc3Npc3QtU2Vzc2lvbkNsZWFudXAnLFxyXG4gICAgICBkZXNjcmlwdGlvbjogJ1RyaWdnZXJzIHNlc3Npb24gY2xlYW51cCBMYW1iZGEgZXZlcnkgMjQgaG91cnMnLFxyXG4gICAgICBzY2hlZHVsZTogZXZlbnRzLlNjaGVkdWxlLnJhdGUoY2RrLkR1cmF0aW9uLmhvdXJzKDI0KSksXHJcbiAgICB9KTtcclxuICAgIFxyXG4gICAgY2xlYW51cFJ1bGUuYWRkVGFyZ2V0KG5ldyB0YXJnZXRzLkxhbWJkYUZ1bmN0aW9uKGNsZWFudXBMYW1iZGEpKTtcclxuXHJcbiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XHJcbiAgICAvLyBBUEkgR2F0ZXdheSB3aXRoIFRMUyAxLjIrLCBDbG91ZFdhdGNoIExvZ2dpbmcsIGFuZCBDT1JTXHJcbiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XHJcbiAgICBcclxuICAgIGNvbnN0IGFwaSA9IG5ldyBhcGlnYXRld2F5LlJlc3RBcGkodGhpcywgJ01lZEFzc2lzdEFQSScsIHtcclxuICAgICAgcmVzdEFwaU5hbWU6ICdNZWRBc3Npc3QgQVBJJyxcclxuICAgICAgZGVzY3JpcHRpb246ICdBUEkgZm9yIE1lZEFzc2lzdCBBSSBTeXN0ZW0nLFxyXG4gICAgICBkZXBsb3lPcHRpb25zOiB7XHJcbiAgICAgICAgc3RhZ2VOYW1lOiAncHJvZCcsXHJcbiAgICAgICAgbG9nZ2luZ0xldmVsOiBhcGlnYXRld2F5Lk1ldGhvZExvZ2dpbmdMZXZlbC5JTkZPLFxyXG4gICAgICAgIGRhdGFUcmFjZUVuYWJsZWQ6IHRydWUsXHJcbiAgICAgICAgbWV0cmljc0VuYWJsZWQ6IHRydWUsXHJcbiAgICAgIH0sXHJcbiAgICAgIGRlZmF1bHRDb3JzUHJlZmxpZ2h0T3B0aW9uczoge1xyXG4gICAgICAgIGFsbG93T3JpZ2luczogWycqJ10sXHJcbiAgICAgICAgYWxsb3dNZXRob2RzOiBhcGlnYXRld2F5LkNvcnMuQUxMX01FVEhPRFMsXHJcbiAgICAgICAgYWxsb3dIZWFkZXJzOiBbJyonXSxcclxuICAgICAgICBhbGxvd0NyZWRlbnRpYWxzOiBmYWxzZSxcclxuICAgICAgICBzdGF0dXNDb2RlOiAyMDAsXHJcbiAgICAgIH0sXHJcbiAgICAgIGVuZHBvaW50Q29uZmlndXJhdGlvbjoge1xyXG4gICAgICAgIHR5cGVzOiBbYXBpZ2F0ZXdheS5FbmRwb2ludFR5cGUuUkVHSU9OQUxdLFxyXG4gICAgICB9LFxyXG4gICAgICBwb2xpY3k6IG5ldyBpYW0uUG9saWN5RG9jdW1lbnQoe1xyXG4gICAgICAgIHN0YXRlbWVudHM6IFtcclxuICAgICAgICAgIG5ldyBpYW0uUG9saWN5U3RhdGVtZW50KHtcclxuICAgICAgICAgICAgZWZmZWN0OiBpYW0uRWZmZWN0LkFMTE9XLFxyXG4gICAgICAgICAgICBwcmluY2lwYWxzOiBbbmV3IGlhbS5BbnlQcmluY2lwYWwoKV0sXHJcbiAgICAgICAgICAgIGFjdGlvbnM6IFsnZXhlY3V0ZS1hcGk6SW52b2tlJ10sXHJcbiAgICAgICAgICAgIHJlc291cmNlczogWydleGVjdXRlLWFwaTovKiddLFxyXG4gICAgICAgICAgICBjb25kaXRpb25zOiB7XHJcbiAgICAgICAgICAgICAgU3RyaW5nRXF1YWxzOiB7XHJcbiAgICAgICAgICAgICAgICAnYXdzOlNlY3VyZVRyYW5zcG9ydCc6ICd0cnVlJywgLy8gRW5mb3JjZSBUTFNcclxuICAgICAgICAgICAgICB9LFxyXG4gICAgICAgICAgICB9LFxyXG4gICAgICAgICAgfSksXHJcbiAgICAgICAgXSxcclxuICAgICAgfSksXHJcbiAgICB9KTtcclxuXHJcbiAgICAvLyBBUEkgRW5kcG9pbnRzIHdpdGggTGFtYmRhIHByb3h5IGludGVncmF0aW9uIChMYW1iZGEgcmV0dXJucyBDT1JTIGhlYWRlcnMpXHJcbiAgICAvLyBDT1JTIGlzIGhhbmRsZWQgYnkgZGVmYXVsdENvcnNQcmVmbGlnaHRPcHRpb25zIGF0IEFQSSBsZXZlbFxyXG4gICAgY29uc3QgdXBsb2FkUmVzb3VyY2UgPSBhcGkucm9vdC5hZGRSZXNvdXJjZSgndXBsb2FkJyk7XHJcbiAgICB1cGxvYWRSZXNvdXJjZS5hZGRNZXRob2QoJ1BPU1QnLCBuZXcgYXBpZ2F0ZXdheS5MYW1iZGFJbnRlZ3JhdGlvbih1cGxvYWRMYW1iZGEsIHtcclxuICAgICAgcHJveHk6IHRydWUsXHJcbiAgICB9KSk7XHJcblxyXG4gICAgY29uc3QgY2hhdFJlc291cmNlID0gYXBpLnJvb3QuYWRkUmVzb3VyY2UoJ2NoYXQnKTtcclxuICAgIGNoYXRSZXNvdXJjZS5hZGRNZXRob2QoJ1BPU1QnLCBuZXcgYXBpZ2F0ZXdheS5MYW1iZGFJbnRlZ3JhdGlvbihyYWdMYW1iZGEsIHtcclxuICAgICAgcHJveHk6IHRydWUsXHJcbiAgICB9KSk7XHJcblxyXG4gICAgY29uc3QgZGFzaGJvYXJkUmVzb3VyY2UgPSBhcGkucm9vdC5hZGRSZXNvdXJjZSgnZGFzaGJvYXJkJyk7XHJcbiAgICBkYXNoYm9hcmRSZXNvdXJjZS5hZGRNZXRob2QoJ0dFVCcsIG5ldyBhcGlnYXRld2F5LkxhbWJkYUludGVncmF0aW9uKGRhc2hib2FyZExhbWJkYSwge1xyXG4gICAgICBwcm94eTogdHJ1ZSxcclxuICAgIH0pKTtcclxuXHJcbiAgICBjb25zdCBleHBvcnRSZXNvdXJjZSA9IGFwaS5yb290LmFkZFJlc291cmNlKCdleHBvcnQnKTtcclxuICAgIGV4cG9ydFJlc291cmNlLmFkZE1ldGhvZCgnUE9TVCcsIG5ldyBhcGlnYXRld2F5LkxhbWJkYUludGVncmF0aW9uKGV4cG9ydExhbWJkYSwge1xyXG4gICAgICBwcm94eTogdHJ1ZSxcclxuICAgIH0pKTtcclxuXHJcbiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XHJcbiAgICAvLyBPdXRwdXRzXHJcbiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XHJcbiAgICBcclxuICAgIG5ldyBjZGsuQ2ZuT3V0cHV0KHRoaXMsICdBUElFbmRwb2ludCcsIHtcclxuICAgICAgdmFsdWU6IGFwaS51cmwsXHJcbiAgICAgIGRlc2NyaXB0aW9uOiAnQVBJIEdhdGV3YXkgZW5kcG9pbnQgVVJMJyxcclxuICAgICAgZXhwb3J0TmFtZTogJ01lZEFzc2lzdEFQSUVuZHBvaW50JyxcclxuICAgIH0pO1xyXG5cclxuICAgIG5ldyBjZGsuQ2ZuT3V0cHV0KHRoaXMsICdEb2N1bWVudHNCdWNrZXROYW1lJywge1xyXG4gICAgICB2YWx1ZTogZG9jdW1lbnRzQnVja2V0LmJ1Y2tldE5hbWUsXHJcbiAgICAgIGRlc2NyaXB0aW9uOiAnUzMgYnVja2V0IGZvciBkb2N1bWVudHMnLFxyXG4gICAgICBleHBvcnROYW1lOiAnTWVkQXNzaXN0RG9jdW1lbnRzQnVja2V0JyxcclxuICAgIH0pO1xyXG5cclxuICAgIG5ldyBjZGsuQ2ZuT3V0cHV0KHRoaXMsICdTZXNzaW9uVGFibGVOYW1lJywge1xyXG4gICAgICB2YWx1ZTogc2Vzc2lvblRhYmxlLnRhYmxlTmFtZSxcclxuICAgICAgZGVzY3JpcHRpb246ICdEeW5hbW9EQiB0YWJsZSBmb3Igc2Vzc2lvbnMnLFxyXG4gICAgICBleHBvcnROYW1lOiAnTWVkQXNzaXN0U2Vzc2lvblRhYmxlJyxcclxuICAgIH0pO1xyXG4gIH1cclxufVxyXG4iXX0=