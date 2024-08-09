# %% [markdown]
# ## SageMaker Pipeline
# 
# ![ML pipeline](img/sagemaker_pipeline.png)

# %% [markdown]
# ## Dataset
# 
# [SageMaker Examples](https://github.com/aws/amazon-sagemaker-examples/tree/main) To get relevant solutions to common tasks
# 
# The dataset you use is the [UCI Machine Learning Abalone Dataset](https://archive.ics.uci.edu/ml/datasets/abalone) [1].  The aim for this task is to determine the age of an abalone snail from its physical measurements. At the core, this is a regression problem.
# 
# ![Abalone Snail](img/abalone.png)
# 
# The dataset contains several features: length, diameter, height, whole_weight, gender and rings.
# 
# The number of rings turns out to be a good approximation for age (age is rings + 1.5). However, to obtain this number requires cutting the shell through the cone, staining the section, and counting the number of rings through a microscope, which is a time-consuming task. However, the other physical measurements are easier to determine. You use the dataset to build a predictive model of the variable rings through these other physical measurements.

# %% [markdown]
# # Setup

# %%
# ! pip install -U sagemaker

# %% [markdown]
# # ADD USER ID

# %%
import os
USER_ID = os.getenv("USER_ID")

# %%
import sagemaker
import boto3
from botocore.exceptions import ClientError
from sagemaker.workflow.pipeline_context import PipelineSession


s3_bucket = f"{USER_ID}-av-llmops-sagemaker-workshop"
role_name = "llmops_workshop_sagemaker_exec_role "

train_instance = 'ml.g5.2xlarge'
process_instance = 'ml.t3.xlarge'

preprocess_job_name = f"{USER_ID}-abalone-preprocess"
train_job_name = f"{USER_ID}-abalone-train"
eval_job_name = f"{USER_ID}-abalone-eval"
model_name = f"{USER_ID}-abalone-model"
model_package_group_name = f"{USER_ID}AbaloneModelPackageGroupName"
pipeline_name = f"{USER_ID}-AbalonePipeline"

region = "ap-south-1"
mean_square_error_threshold = 6.0

# s3_bucket = sess.default_bucket()
def create_bucket(bucket_name, region="ap-south-1"):
    s3_client = boto3.client('s3', region_name=region)
    try:
        location = {'LocationConstraint': region}
        s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
    except ClientError as e:
        print(f"Bucket {bucket_name} got response {e.response['Error']['Code']}")

create_bucket(s3_bucket)

try:
    role = sagemaker.get_execution_role()
except ValueError:
    iam = boto3.client('iam')
    role = "arn:aws:iam::009676737623:role/llmops_workshop_sagemaker_exec_role"

base_uri = f"s3://{s3_bucket}/abalone"
model_path = f"s3://{s3_bucket}/AbaloneTrain"

pipeline_session = PipelineSession(default_bucket=s3_bucket)

print(f"{role =}")
print(f"{s3_bucket =}")
print(f"{region =}")

# %% [markdown]
# # Sync Dataset

# %%
# ! mkdir -p data

# %%
local_path = "./data/abalone-dataset.csv"

s3 = boto3.resource("s3")
s3.Bucket(f"sagemaker-example-files-prod-{region}").download_file(
    "datasets/tabular/uci_abalone/abalone.csv", local_path
)

input_data_uri = sagemaker.s3.S3Uploader.upload(
    local_path=local_path,
    desired_s3_uri=base_uri,
)
print(input_data_uri)

# %% [markdown]
# # Global Parameters

# %%
from sagemaker.workflow.parameters import (
    ParameterInteger,
    ParameterString,
    ParameterFloat,
)

processing_instance_count = ParameterInteger(name="ProcessingInstanceCount", default_value=1)
instance_type = ParameterString(name="ProcessingInstanceType", default_value=process_instance)
train_instance_type = ParameterString(name="TrainingInstanceType", default_value=train_instance)
model_approval_status = ParameterString(name="ModelApprovalStatus", default_value="PendingManualApproval")
input_data = ParameterString(name="InputData",default_value=input_data_uri)
mse_threshold = ParameterFloat(name="MseThreshold", default_value=mean_square_error_threshold)

# %% [markdown]
# # Processing Step for Feature Engineering
# 
#  `scikit-learn` to do the following:
# 
# * Fill in missing data.
# * Scale and normalize all numerical fields.
# * Split the data into training, validation, and test datasets.
# 
# ![ML pipeline](img/sagemaker_pipeline.png)
# 

# %% [markdown]
# # PREPROCESSING FILE at code/preprocessing.py

# %%
from sagemaker.sklearn.processing import SKLearnProcessor


framework_version = "1.2-1"

sklearn_processor = SKLearnProcessor(
    framework_version=framework_version,
    instance_type=instance_type,
    instance_count=processing_instance_count,
    base_job_name=preprocess_job_name,
    role=role,
    sagemaker_session=pipeline_session,
)

# %%
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.workflow.steps import ProcessingStep

processor_args = sklearn_processor.run(
    inputs=[
        ProcessingInput(source=input_data, destination="/opt/ml/processing/input"),
    ],
    outputs=[
        ProcessingOutput(output_name="train", source="/opt/ml/processing/train"),
        ProcessingOutput(output_name="validation", source="/opt/ml/processing/validation"),
        ProcessingOutput(output_name="test", source="/opt/ml/processing/test"),
    ],
    code="code/preprocessing.py",
)

step_process = ProcessingStep(name="AbaloneProcess", step_args=processor_args)

# %% [markdown]
# # Training Step
# 
# [ProcessingJob Parameters](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_DescribeProcessingJob.html)
# 
# ![ML pipeline](img/sagemaker_pipeline.png)

# %%
from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput

image_uri = sagemaker.image_uris.retrieve(
    framework="xgboost",
    region=region,
    version="1.0-1",
    py_version="py3",
    instance_type=instance_type
)
# image_uri = "720646828776.dkr.ecr.ap-south-1.amazonaws.com/sagemaker-xgboost:1.0-1-cpu-py3"

xgb_train = Estimator(
    base_job_name=train_job_name,
    image_uri=image_uri,
    instance_type=train_instance_type,
    instance_count=1,
    output_path=model_path,
    role=role,
    sagemaker_session=pipeline_session,
)
xgb_train.set_hyperparameters(
    objective="reg:linear",
    num_round=10,
    max_depth=5,
    eta=0.2,
    gamma=4,
    min_child_weight=6,
    subsample=0.7,
)

train_args = xgb_train.fit(
    inputs={
        "train": TrainingInput(
            s3_data=step_process.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri,
            content_type="text/csv",
        ),
        "validation": TrainingInput(
            s3_data=step_process.properties.ProcessingOutputConfig.Outputs[
                "validation"
            ].S3Output.S3Uri,
            content_type="text/csv",
        ),
    }
)

# %%
from sagemaker.inputs import TrainingInput
from sagemaker.workflow.steps import TrainingStep


step_train = TrainingStep(
    name="AbaloneTrain",
    step_args=train_args,
)

# %% [markdown]
# ## Evaluation Step
# 
# * Load the model.
# * Read the test data.
# * Issue predictions against the test data.
# * Build a classification report, including accuracy and ROC curve.
# * Save the evaluation report to the evaluation directory.
# 
# ![ML pipeline](img/sagemaker_pipeline.png)

# %% [markdown]
# # EVALUATION FILE at code/evaluation.py

# %%
from sagemaker.processing import ScriptProcessor

script_eval = ScriptProcessor(
    image_uri=image_uri,
    command=["python3"],
    instance_type=instance_type,
    instance_count=1,
    base_job_name=eval_job_name,
    role=role,
    sagemaker_session=pipeline_session,
)

eval_args = script_eval.run(
    inputs=[
        ProcessingInput(
            source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
            destination="/opt/ml/processing/model",
        ),
        ProcessingInput(
            source=step_process.properties.ProcessingOutputConfig.Outputs["test"].S3Output.S3Uri,
            destination="/opt/ml/processing/test",
        ),
    ],
    outputs=[
        ProcessingOutput(output_name="evaluation", source="/opt/ml/processing/evaluation"),
    ],
    code="code/evaluation.py",
)

# %%
from sagemaker.workflow.properties import PropertyFile


evaluation_report = PropertyFile(
    name="EvaluationReport", output_name="evaluation", path="evaluation.json"
)
step_eval = ProcessingStep(
    name="AbaloneEval",
    step_args=eval_args,
    property_files=[evaluation_report],
)

# %% [markdown]
# # Model Step
# - Register vs Model vs Model Package
# - ![ML pipeline](img/sagemaker_pipeline.png)

# %%
from sagemaker.model import Model

model = Model(
    name=model_name,
    image_uri=image_uri,
    model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
    sagemaker_session=pipeline_session,
    role=role,
)

# %%
from sagemaker.model_metrics import MetricsSource, ModelMetrics
from sagemaker.inputs import CreateModelInput
from sagemaker.workflow.model_step import ModelStep


model_metrics = ModelMetrics(
    model_statistics=MetricsSource(
        s3_uri="{}/evaluation.json".format(
            step_eval.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"]["S3Uri"]
        ),
        content_type="application/json",
    )
)

register_args = model.register(
    content_types=["text/csv"],
    response_types=["text/csv"],
    inference_instances=list(set(["ml.t2.medium", "ml.m5.xlarge", "ml.g5.2xlarge"])),
    transform_instances=["ml.m5.xlarge"],
    model_package_group_name=model_package_group_name,
    approval_status=model_approval_status,
    model_metrics=model_metrics,
)
step_register = ModelStep(name="AbaloneRegisterModel", step_args=register_args)

# %% [markdown]
# # Fail Step

# %%
from sagemaker.workflow.fail_step import FailStep
from sagemaker.workflow.functions import Join

step_fail = FailStep(
    name="AbaloneMSEFail",
    error_message=Join(on=" ", values=["Execution failed due to MSE >", mse_threshold]),
)

# %% [markdown]
# # Condition Step
# 
# ![ML pipeline](img/sagemaker_pipeline.png)

# %%
from sagemaker.workflow.conditions import ConditionLessThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet

# Sagemaker helper function to extract values from Json documents
cond_lte = ConditionLessThanOrEqualTo(
    left=JsonGet(
        step_name=step_eval.name,
        property_file=evaluation_report,
        json_path="regression_metrics.mse.value",
    ),
    right=mse_threshold,
)

step_cond = ConditionStep(
    name="AbaloneMSECond",
    conditions=[cond_lte],
    if_steps=[step_register],
    else_steps=[step_fail],
)

# %% [markdown]
# # Create Pipeline

# %%
from sagemaker.workflow.pipeline import Pipeline

pipeline = Pipeline(
    name=pipeline_name,
    parameters=[
        processing_instance_count,
        instance_type,
        train_instance_type,
        model_approval_status,
        input_data,
        mse_threshold,
    ],
    steps=[step_process, step_train, step_eval, step_cond],
)

# %% [markdown]
# # Start Pipeline

# %%
pipeline.upsert(role_arn=role)

# %% [markdown]
# Start the pipeline and accept all the default parameters.

# %%
execution = pipeline.start(
    parameters={"MseThreshold": 3.0}
)

# %%
# execution.describe()

# # %%
# try:
#     execution.wait()
#     execution.list_steps()
# except Exception as error:
#     print(error)

# %%
