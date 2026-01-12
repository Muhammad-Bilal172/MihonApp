from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from database import *
from Auth.create_jwt_token import *
from Auth.register import *
from Auth.login import *
from Auth.logout import *
from Auth.forgot_password import *
from Auth.reset_password import *
from Auth.refresh_func import *
from Auth.verify_email import *
from security import *
from MangaScrap.getMangasName import *
from MangaScrap.addExtension import *
from MangaScrap.scrapeChapersList import *
from MangaScrap.scrapeChapterImages import *
from MangaScrap.library import *
from History.view_manga_history import *
from MoreFeatures.moreFeautures import *
from MoreFeatures.statistics import *
from MoreFeatures.categories import *
from MoreFeatures.settings import *
from MangaScrap.search import *
from MoreFeatures.SettingApis.appearence import *
from MoreFeatures.SettingApis.library_settings import *


app = FastAPI()
setup_database()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def main():
    return RedirectResponse("/login", status_code=303)

reset_password_func(app)
login_page(app)
logout_func(app)
register_page(app)
resend_email_code(app)
reset_pass_func(app)
verify_email_func(app)
scrapePage(app)
add_extension_func(app)
scrape_chapter_list_func(app)
scrape_chapters_func(app)
library_func(app)
soruce_func(app)
view_manga_history_func(app)
more_feautures_func(app)
get_statistics_func(app)
categories_func(app)
setting_func(app)
search_func(app)
appearence_func(app)
library_settings_func(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)