import datetime
import logging
import os
import webapp2

from beers import beers
from beeruser import BeerUser

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import urlfetch

###############################################################################
# We'll just use this convenience function to retrieve and render a template.
def render_template(handler, templatename, templatevalues={}):
  path = os.path.join(os.path.dirname(__file__), 'templates/' + templatename)
  html = template.render(path, templatevalues)
  handler.response.out.write(html)


###############################################################################
# We'll use this convenience function to retrieve the current user's email.
def get_user_email():
  result = None
  user = users.get_current_user()
  if user:
    result = user.email()
  return result

# This function returns the balance remaining in user's account
def get_user_balance(email):
    beerUser = ndb.Key("BeerUser", email).get()
    if beerUser is None:
      return 0.0
    else:
      return beerUser.balance

# This function returns the address stored in user's account
def get_user_address(email):
    beerUser = ndb.Key("BeerUser", email).get()
    if beerUser is None:
      return "No entry"
    else:
      return beerUser.address

###############################################################################
class VerifyAgePageHandler(webapp2.RequestHandler):
  def get(self):
    render_template(self, 'verifyage.html', {})
    
  def post(self):
    val = int(self.request.get("ageInput_form"));
    if val == 1:
      self.redirect("/home")
    else:
      self.redirect("http://www.toysrus.com/");
	
###############################################################################
class MainPageHandler(webapp2.RequestHandler):
  def get(self):
    email = get_user_email()
    page_params = {
      'user_email': email,
      'login_url': users.create_login_url('/home'),
      'logout_url': users.create_logout_url('/home')
    }
    render_template(self, 'home.html', page_params)
  
###############################################################################
class OrderPageHandler(webapp2.RequestHandler):
  def get(self):
    render_template(self, 'order.html') 
  
###############################################################################
class AccountPageHandler(webapp2.RequestHandler):
  def get(self):
    email = get_user_email()
    if email:
      # query ndb to get funds
      balance = get_user_balance(email)
      
      page_params = {
        'user_email': email,
        'balance': balance
      }
      render_template(self, 'account.html', page_params)
    else:
      self.redirect(users.create_login_url('/account'))


###############################################################################
class LoadFundsPageHandler(webapp2.RequestHandler):
  def get(self):
    email = get_user_email()	  
    if email:
      balance = get_user_balance(email)
      address = get_user_address(email)
      
      process_url = blobstore.create_upload_url('/loadfunds_process')
      page_params = {
        'user_email': email,
        'balance': balance,
        'loadfunds_process_url': process_url
      }
      render_template(self, 'loadfunds.html', page_params)
    else:
      self.redirect('/home')
      
###############################################################################
class LoadFundsProcessHandler(webapp2.RequestHandler):
  def post(self):
    email = get_user_email()
    if email:
      balance = get_user_balance(email)
      address = get_user_address(email)

      try:
        amount = float(self.request.get('amount'))
      except ValueError:
        self.redirect("loadfunds")
        return
      newBalance = balance + amount
      
      beerUser = BeerUser()
      beerUser.key = ndb.Key("BeerUser", email)
      beerUser.balance = newBalance
      beerUser.address = address
      beerUser.put()
    self.redirect('/account')


###############################################################################
class BeerPageHandler(webapp2.RequestHandler):
  def get(self):
    template_params = {
      'beers' : beers
    }
    render_template(self, 'beer.html', templatevalues=template_params)

###############################################################################
class BeerBreweryPageHandler(webapp2.RequestHandler):
  def get(self):
    template_params = {
      'beers' : sorted(beers, key = lambda beer: beer["brewery"])
    }
    render_template(self, 'beer.html', templatevalues=template_params)

###############################################################################
class BeerNamePageHandler(webapp2.RequestHandler):
  def get(self):
    template_params = {
      'beers' : sorted(beers, key = lambda beer: beer["product"])
    }
    render_template(self, 'beer.html', templatevalues=template_params)

###############################################################################
class BeerStylePageHandler(webapp2.RequestHandler):
  def get(self):
    template_params = {
      'beers' : sorted(beers, key = lambda beer: beer["style"])
    }
    render_template(self, 'beer.html', templatevalues=template_params)

###############################################################################
class BeerAbvPageHandler(webapp2.RequestHandler):
  def get(self):
    template_params = {
      'beers' : sorted(beers, key = lambda beer: float(beer["abv"]))
    }
    render_template(self, 'beer.html', templatevalues=template_params)

###############################################################################
class BeerPricePageHandler(webapp2.RequestHandler):
  def get(self):
    template_params = {
      'beers' : sorted(beers, key = lambda beer: beer["price"])
    }
    render_template(self, 'beer.html', templatevalues=template_params)
  
class GetDistanceHandler(webapp2.RequestHandler):
  def get(self):
    address = self.request.get("address")
    if address:
      # send http request to google maps
      #logging.info(address)
      url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=cathedral%20of%20learning&destinations=" + address + "&mode=driving&language=en-US&units=imperial&key=AIzaSyCXyR3f0rdJZsxwTNaFp2HRFnLUqlOnbvE"
      result = urlfetch.fetch(url)
      #self.response.out.write(address)
      self.response.out.write(result.content)
    else:
      self.response.out.write("")

  def post(self):
    return self.get()

###############################################################################
mappings = [
  ('/', VerifyAgePageHandler),
  ('/home', MainPageHandler), 
  ('/order', OrderPageHandler),
  ('/account', AccountPageHandler),
  ('/loadfunds', LoadFundsPageHandler),
  ('/loadfunds_process', LoadFundsProcessHandler),
  ('/beer', BeerPageHandler),
  ('/beerbrewery', BeerBreweryPageHandler),
  ('/beername', BeerNamePageHandler),
  ('/beerstyle', BeerStylePageHandler),
  ('/beerabv', BeerAbvPageHandler),
  ('/beerprice', BeerPricePageHandler),
  ('/getdistance', GetDistanceHandler)
]
app = webapp2.WSGIApplication(mappings, debug=True)
