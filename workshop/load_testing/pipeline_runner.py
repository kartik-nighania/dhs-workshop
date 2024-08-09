import os
import subprocess
import os
import dotenv

print(dotenv.load_dotenv('./.env'))

def main():
    for user_id in range(1, 51):
        os.environ['USER_ID'] = f"u{user_id}"
        subprocess.run(['python3', 'pipeline.py'])
        print(f"ran pipeline for with {os.getenv('USER_ID')}, {os.getenv('AWS_ACCESS_KEY_ID')}")

if __name__ == "__main__":
    main()