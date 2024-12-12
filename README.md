# Local Computing Breeder Service

A composite service combines atomic services for local testing and GCP deployment.

---

## 🚀 Deployment Instructions

### 1. Local Testing Setup

Follow these steps to deploy the service locally:

#### Step 1: Create an `.env` File

Create an environment file to store your configuration variables:

```bash
vim .env
```

#### Step 2: Add the Following Content to .env

```bash
DATABASE_URL=<ENV>
JWT_SECRET_KEY=<ENV>
JWT_ALGORITHM=<ENV>
JWT_REFRESH_SECRET=<ENV>
CAT_API_KEY=<ENV>
```

#### Step 3: Set up private-pubsub.json and
To allow breeder service receive email notification, we need to set up a private-pubsub.json and private-workflow.json under composite-service/app. The following is a structure of those two json. 
```bash
{
  "type": <TYPE>,
  "project_id": <PROJECT_ID>,
  "private_key_id": <PRIVATE_KEY_ID>,
  "private_key": <Private_Key>,
  "client_email": <Client_email>,
  "client_id": <Client>,
  "auth_uri": <Auth_uri>,
  "token_uri": <Token_uri>,
  "auth_provider_x509_cert_url": <Auth_URL>,
  "client_x509_cert_url": <Client_URL>,
  "universe_domain": "googleapis.com"
}
```

#### Step 4: Activate Docker on Desktop

run the docker container:

```bash
./build.sh
```

The composite service will run on http://localhost:8084/api/v1/composites

### 2. Deploy to GCP

#### Option 1. Deploy through docker container

##### Step 1: Step 1: Create an `prod.env` File

Create an environment file to store your configuration variables:

```bash
vim prod.env
```

##### Step 2: Add the Following Content to prod.env

```bash
DEP_DATABASE_URI=<ENV>
//Change URL_PREFIX to your corresponding ipv4
URL_PREFIX=<ENV>
DATABASE_URI=<ENV>

DB_USER=<ENV>
DB_PASS=<ENV>
DB_NAME=<ENV>
INSTANCE_UNIX_SOCKET=<ENV>
INSTANCE_CONNECTION_NAME=<ENV>
JWT_SECRET_KEY=<ENV>
JWT_ALGORITHM=<ENV>
JWT_REFRESH_SECRET=<ENV>
CAT_API_KEY=<ENV>

```

##### Step 3: Set up private-pubsub.json and
To allow breeder service receive email notification, we need to set up a private-pubsub.json and private-workflow.json under composite-service/app. The following is a structure of those two json. 
```bash
{
  "type": <TYPE>,
  "project_id": <PROJECT_ID>,
  "private_key_id": <PRIVATE_KEY_ID>,
  "private_key": <Private_Key>,
  "client_email": <Client_email>,
  "client_id": <Client>,
  "auth_uri": <Auth_uri>,
  "token_uri": <Token_uri>,
  "auth_provider_x509_cert_url": <Auth_URL>,
  "client_x509_cert_url": <Client_URL>,
  "universe_domain": "googleapis.com"
}
```

##### Step 4: Activate Docker on Desktop

run the docker container:

```bash
docker-compose -f docker-compose.prod.yml --env-file prod.env up --build -d
```

The composite service will run on http://external-ipv4:8084/api/v1/composites

