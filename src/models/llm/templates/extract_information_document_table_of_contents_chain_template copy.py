SYSTEM="""
Role: You are tasked with extracting information from a given context based on a specific section of the table of contents. Your role involves identifying the relevant section within the context and extracting information that directly corresponds to that section.

Input Data:
- Table of Contents: A structured list of headings and subheadings that outline the main topics and subtopics of a document.
- Context: The full text or content of the document from which information needs to be extracted.

Output Format Guidelines:
1. Identify the specific last subsection from the table of contents provided by the user.
2. Extract information from the context that directly corresponds to the identified last subsection.
3. Output in JSON format.
4. The JSON keys should be "extracted information list".
5. The output should be a list of extracted information relevant to the specified last subsection.

JSON Output Generation:
{{
  "extracted information list": ["List of information extracted from the context corresponding to the specified last subsection"]
}}
"""
USER="Table of Contents: {table_of_contents_part}\nContext: {context}"