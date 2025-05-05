# Seat Management Dashboard

A Streamlit-based dashboard for managing and analyzing seat allocation and usage data.

## Features

- Interactive date range filtering
- Team-based filtering
- Key metrics visualization
- Team distribution analysis
- Activity timeline
- Detailed seat information view
- CSV export functionality

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Place your seat data in a file named `data.json` in the same directory as the script
2. Run the dashboard:
```bash
streamlit run seatreport.py
```

## Data Format

The dashboard expects a JSON file with the following structure:
```json
{
    "total_seats": number,
    "seats": [
        {
            "created_at": "datetime",
            "assignee": {
                "login": "string",
                "type": "string",
                ...
            },
            "last_activity_at": "datetime",
            "last_activity_editor": "string",
            "assigning_team": {
                "name": "string",
                ...
            },
            "plan_type": "string"
        },
        ...
    ]
}
```

## Dashboard Sections

1. **Key Metrics**
   - Total Seats
   - Active Users
   - Inactive Users

2. **Team Distribution**
   - Pie chart showing seat distribution across teams

3. **Activity Timeline**
   - Line chart showing daily activity

4. **Detailed View**
   - Tabular view of all seat information
   - Export to CSV functionality

## Deployment

### Local Deployment
1. Follow the installation steps above
2. Run `streamlit run seatreport.py`

### Cloud Deployment
The dashboard can be deployed to various cloud platforms:

#### Streamlit Cloud
1. Push your code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy the app

#### Heroku
1. Create a `Procfile`:
```
web: streamlit run seatreport.py
```
2. Deploy to Heroku:
```bash
heroku create
git push heroku main
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details. 