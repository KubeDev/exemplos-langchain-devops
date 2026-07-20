from langchain_community.agent_toolkits import FileManagementToolkit


def get_tools(root_dir: str):
    toolkit = FileManagementToolkit(
        root_dir=root_dir,
        selected_tools=["read_file", "list_directory", "file_search"],
    )
    return toolkit.get_tools()
