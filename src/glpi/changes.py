from glpi_client import RequestHandler

url = "http://grit.ideasfractal.com"
app_token = "uNDYWQpoTpR5tG6IuixwgPQvgFWwLUIgRthODAMu"
user_token = "IrdleejAfzHtusWw9mVGAXEJBk6lV5DeqyTg2MsD"

with RequestHandler(url, app_token, user_token) as handler:
    print(handler.))


