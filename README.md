# Junior Data Scientist Project

## Introduction

**Your AI-powered assistant for effortless data science!**

The Junior Data Scientist CLI is an AI-powered command-line tool designed to take the grunt work out of your data science projects. Think of it as your very own junior data scientist—ready to handle the baseline tasks so you can focus on solving high-level problems.

## Installing the Tool

To install the tool, clone the repository and install it in editable mode:

```bash
git clone https://github.com/vishalrk1/junior-scientist-agent.git
cd junior-data-scientist
pip install -e .
```

## Creating a New Project

You can create a new project using the following command:

```bash
buddy new --name <project_name>
```

Replace `<project_name>` with the desired name for your new project.

## Starting project and chat

```bash
cd projects/<project_name>
buddy start
```

# TODO

- [ ] Add caching for prompts and reports on project level
- [ ] Add global memory module
- [x] Generating reports for data cleaning stpes and business insights for csv files
- [x] load/save reports
- [x] ML workflow planner agent
- [ ] Chat with planner to improve plan 
- [ ] create api end points `buddy server`
- [ ] create frontend to interact with agents