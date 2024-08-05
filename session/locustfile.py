# locust -f ./locustfile.py  
# locust -f ./locustfile.py --headless --users 100 --spawn-rate 10
from json import JSONDecodeError
from locust import HttpUser, task, between

class QuickstartUser(HttpUser):

    # wait time between each task
    host = "http://13.200.76.82:8000"
    wait_time = between(1,2)

    @task
    def call_sql_generator(self):
        adapter_path = "predibase/gsm8k"
        prompt = """Your task is a Named Entity Recognition (NER) task. \n\
            Predict the category of each entity, then place the entity into the list associated with the category in an output JSON payload.\n\
            Below is an example: \n\
            Input: EU rejects German call to boycott British lamb.\n\
            Output: {"person": [], "organization": ["EU"], "location": [], "miscellaneous": ["German", "British"]} \n\
            Now, complete the task. \n\ 
            Input: By the close Yorkshire had turned that into a 37-run advantage but off-spinner David had scuttled their hopes, \
                taking four for 24 in 48 balls and leaving them hanging on 119 for five and praying for rain. \n\
            Output:"""
        
        expected_output = '{"person": [], "organization": [], "location": ["Yorkshire"], "miscellaneous": ["David"]}'

        with self.client.post("/generate",
            name="call_sql_generator",
            headers={"Content-Type": "application/json"},
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 512,
                    "adapter_id": adapter_path,
                    "adapter_source": "hub",
                    "temperature": 0,
                    "top_p": 0.1,
                    }
            },
            catch_response=True
        ) as response:
            try:
                if response.json()["generated_text"] != expected_output:
                    response.failure("Did not get expected value")
            except JSONDecodeError:
                response.failure("Response could not be decoded as JSON")
            except KeyError as e:
                response.failure(e)

    @task
    def call_customer_support(self):
        adapter_path = "predibase/customer_support"
        prompt = """Consider the case of a customer contacting the support center.
            The term 'task type' refers to the reason for why the customer contacted support.
            ### The possible task types are: ### 
            - replace card
            - transfer money
            - check balance
            - order checks
            - pay bill
            - reset password
            - schedule appointment
            - get branch hours
            - none of the above

            Summarize the issue/question/reason that drove the customer to contact support:

            ### Transcript: [noise] [noise] [noise] [noise] hello hello hi i'm sorry this this call uh hello this is harper valley national bank my name is dawn how can i help you today hi oh okay my name is jennifer brown and i need to check my account balance if i could [noise] [noise] [noise] [noise] what account would you like to check um [noise] uhm my savings account please [noise] [noise] oh but the way that you're doing one moment hello yeah one moment uh huh no problem [noise] your account balance is eighty two dollars is there anything else i can help you with no i don't think so thank you so much you were very helpful thank you have a good day bye bye [noise] you too 

            ### Task Type:
            test_transcript ="""
        
        expected_output = "check balance"

        with self.client.post("/generate",
            name="call_customer_support",
            headers={"Content-Type": "application/json"},
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 512,
                    "adapter_id": adapter_path,
                    "adapter_source": "hub",
                    "temperature": 0,
                    "top_p": 0.1,
                    }
            },
            catch_response=True
        ) as response:
            try:
                if response.json()["generated_text"] != expected_output:
                    response.failure("Did not get expected value")
            except JSONDecodeError:
                response.failure("Response could not be decoded as JSON")
            except KeyError as e:
                response.failure(e)

    @task
    def call_wikisql(self):
        adapter_path = "predibase/magicoder"

        prompt = """Sample input: Below is a programming problem, paired with a language in which the solution should be written. \
            Write a solution in the provided that appropriately solves the programming problem. \
            ### Problem: def strlen(string: str) -> int: ''' Return length of given string >>> strlen('') 0 >>> strlen('abc') 3 ''' \
            ### Language: python \
            ### Solution:"""

        expected_output = "def strlen(string: str) -> int:\n    return len(string)"

        with self.client.post("/generate",
            name="call_wikisql",
            headers={"Content-Type": "application/json"},
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 512,
                    "adapter_id": adapter_path,
                    "adapter_source": "hub",
                    "temperature": 0,
                    "top_p": 0.1,
                    }
            },
            catch_response=True
        ) as response:
            try:
                if response.json()["generated_text"] != expected_output:
                    response.failure("Did not get expected value")
            except JSONDecodeError:
                response.failure("Response could not be decoded as JSON")
            except KeyError as e:
                response.failure(e)
