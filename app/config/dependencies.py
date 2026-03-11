from fastapi.templating import Jinja2Templates
from datetime import datetime

# Datetime re-formatting
def dt_reformat(dt):
    return datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M')

# Templates
templates = Jinja2Templates(directory="templates")
templates.env.filters['dt_reformat'] = dt_reformat