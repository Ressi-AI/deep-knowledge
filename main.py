from dotenv import load_dotenv
load_dotenv()
from deep_knowledge.summary import Summary
from langchain_openai import ChatOpenAI


def main():
    llm = 'auto'  # llm = ChatOpenAI(model_name="gpt-4o")
    s = Summary(
        llm=llm,
        input_path='/path/to/book.pdf',
        stream=True,
        extra_instructions="This summary should be very detailed (more than 5000-7000 words)",
    )
    s.run()
    with open("output.md", "w") as f:
        f.write(s.output)
    return


if __name__ == "__main__":
    main()
