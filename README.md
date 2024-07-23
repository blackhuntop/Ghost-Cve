# Ghost-Cve
GitHub CVE Repository Hunt

Hey hackers! 🕵️‍♂️

We’ve got a tool to help you dive into the world of CVEs on GitHub without getting lost. With this bad boy, you can search for repositories related to CVEs and clone them to your own system. Ready for some action? Here’s how you use it:
📦 Prerequisites

Before you dive in, make sure you’ve got these Python libraries installed. They’re required for the tool to run:

    pip install requests rich tzlocal

🚀 Setup

Clone the Repository:

First off, clone our repo to your local machine. Run:

     git clone <URL-OF-THIS-REPOSITORY>
            
Install Dependencies and Run the Script:

After cloning, navigate to the project directory and run the script. It’ll automatically handle the dependencies for you:

    python Ghost-Cve.py

🔍 How to Use

Once you fire up the script, you’ll get a menu like this:

    Search for a Specific CVE:
        Enter the CVE ID you’re interested in and see which repositories are linked to it.

    Search for New CVEs:
        Find CVEs that have been created since your last search.

    Search for CVEs by Date:
        Input a specific date and hunt down CVEs created on that day.

    Search Repositories by Keyword:
        Type in some keywords and see what repositories pop up.

    Help:
        Get more info on the menu options.

    Exit:
        Choose this to quit the program.

⚙️ Settings

    GitHub Token:
        You’ll need to input your GitHub token to use the tool. The script will save this token for future use.

    Settings Files:
        settings.json: Stores your GitHub token.
        last_search.json: Keeps track of the last search time.

This project is licensed under the MIT License.
