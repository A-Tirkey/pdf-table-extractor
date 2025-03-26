# PDF Table Extractor

A web application that extracts tables from PDF files and exports them to an Excel spreadsheet.

## Features

- Upload PDF files and extract tables
- Download extracted tables as an Excel (.xlsx) file
- Responsive and user-friendly interface
- Error handling for invalid files and server issues

## Technologies Used

### Frontend
- React.js
- Axios (for API calls)
- CSS (for styling)

### Backend
- Python Flask
- [Tabula-py](https://github.com/chezou/tabula-py) (for PDF table extraction)
- [OpenPyXL](https://openpyxl.readthedocs.io/) (for Excel file creation)

## Installation

### Prerequisites
- Node.js (for frontend)
- Python 3.7+ (for backend)
- npm or yarn

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/A-Tirkey/pdf-table-extractor.git
   cd pdf-table-extractor
