# ClientManager
This application serves as a tool to stay updated on various companies, helping individuals maintain relationships with these companies or stay informed about their latest news.

---

## **The Problem Being Solved**
Imagine you want to maintain a basic relationship with hundreds of companies or hold stock in these companies and need to stay informed about important events happening within them. 

Using platforms like StockTwits or Seeking Alpha can be cumbersome and tedious when dealing with hundreds of companies. It becomes challenging to sift through what is recent, what is outdated, and to even add all those companies in the first place. Managing such a large volume of information quickly turns into a hassle.

---

## **How This Application Helps**
This tool simplifies the process by consolidating and streamlining updates, allowing users to efficiently monitor multiple companies without the overwhelming clutter or complexity of existing platforms. 

It eliminates the need for manual tracking and makes it easier to prioritize and stay informed about relevant events. The application is lightweight, and its sole purpose is to inform you of any events or news on these companies. It summarizes press releases using a fine-tuned **BART-5 LLM** for concise and clear insights.

---

## **Features**
- **Add Companies**: Add a company using its ticker or CIK code.
- **Delete Companies**: Remove a company from the tracked list.
- **Search Companies**: Quickly search for a company by its ticker.
- **Scan for Updates**: Fetch the latest press release data for all tracked companies.
- **Display Information**:
  - **Ticker/CIK**: Identifier of the company.
  - **Company Name**: Name of the company.
  - **Previous Press Release Date**: Date of the last press release.
  - **Contents**: Summary of the press release.
  - **Press Release Link**: A link to the full press release.
- **Highlight Updates**: Rows with new press release updates are highlighted for quick review.
- **Interactive Actions**:
  - **View Full Summary**: Double-click on the contents to open a detailed popup.
  - **Open Press Release Link**: Double-click on the link to open it in the browser.
- **Automatic Scanning**: Automatically scans all companies for updates when the app starts.

---

## **How It Works**

### **Managing Companies**
1. **Add a Company**:
   - Enter the company’s ticker (e.g., `AAPL`) or CIK code in the input field.
   - Click **"Add Client"** to fetch and display the company’s data.

2. **Delete a Company**:
   - Select a row in the table and click **"Delete Client"** to remove the company from the database.

3. **Search for a Company**:
   - Enter a ticker/CIK name in the input field.
   - Click **"Search Client"** to filter the displayed companies.

---

### **Monitoring Updates**
1. **Scan for Updates**:
   - Click **"Scan for Updates"** to fetch the latest press release data for all tracked companies.
   - Rows with new updates will be **highlighted in yellow**.

2. **Review Updates**:
   - Double-click on the **Contents** column to open a popup with the full summary.
   - Double-click on the **Press Release Link** column to open the link in the browser.
   - Once reviewed, the highlighting for the company is removed.

---

### Main Dashboard
![image](https://github.com/user-attachments/assets/a4b82539-56c5-4bd5-8684-6ca56a9f3c5c)

### Detailed Summary Popup
![image](https://github.com/user-attachments/assets/6ba46eba-6a25-40a2-bd81-6dec268f6e51)

---

## **Notes**
1. **US Companies Only**:
   - This application currently only supports **US-based companies** listed on major US stock exchanges.

2. **8-K Based Data**:
   - The data is primarily extracted from **8-K filings**. While this captures significant events and announcements, smaller press releases or updates might not be included.
   - The app focuses on **big and important releases**, so users should not rely on it for minor updates.

3. **Volatile Schema**:
   - The schema for press releases and filings can vary significantly between companies. This may lead to inconsistencies or errors in data extraction.
   - Expect some bugs during the initial usage, especially for companies with unique or non-standard filing formats.

---

