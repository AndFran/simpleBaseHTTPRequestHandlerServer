from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi


from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine


Base = declarative_base()

class Restaurant(Base):
    __tablename__ = 'restaurant'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=True)

class MenuItem(Base):
    __tablename__ = 'menu_item'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=False)
    course = Column(String(250))
    description = Column(String(250))
    price = Column(String(250))
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    restaurant = relationship(Restaurant)


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.create_all(engine)


# now create a session
DBSession = sessionmaker(bind=engine)

session = DBSession()


def create_restaurant(rest_name):
    r = Restaurant(name=rest_name)
    session.add(r)
    session.commit()
    print "restaurant commited"


def update_restaurant(rest_id, new_rest_name):
    if new_rest_name is None or len(new_rest_name) == 0:
        raise ValueError("Empty name")

    rest = session.query(Restaurant).filter_by(id=rest_id).one()
    rest.name = new_rest_name
    session.add(rest)
    session.commit()
    print "Updated restaurant"

def delete_restaurant(rest_id):
    rest = session.query(Restaurant).filter_by(id=rest_id).one()
    session.delete(rest)
    session.commit()
    print(rest_id, "deleted")




def new_restaurant_form():
    output = '<html><body>'
    output += "<h3>Create a new restaurant:</h3>"
    output += "<form method='POST' enctype='multipart/form-data'>"
    output += "<input type='text' name='restaurant_name'></input>"
    output += "<br>"
    output += "<input type='submit' value='submit'></input>"

    output += "</form>"
    output += '</body></html>'
    return output


def edit_restaurant_form(restaurant_id, restaurant_name):
    output = '<html><body>'
    output += "<h3>Create a new restaurant:</h3>"
    output += "<form method='POST' enctype='multipart/form-data'>"
    output += "<input type='text' name='restaurant_name' value='%s'></input>" % restaurant_name
    output += "<input type='hidden' name='restaurant_id' value='%s'></input>" % restaurant_id
    output += "<br>"
    output += "<input type='submit' value='submit'></input>"

    output += "</form>"
    output += '</body></html>'
    return output


def delete_restaurant_form(restaurant_id, restaurant_name):
    output = '<html><body>'
    output += "<h3>Delete a restaurant:</h3>"
    output += "<p>Are you sure you want to delete %s ?" % restaurant_name
    output += "<form method='POST' enctype='multipart/form-data'>"
    output += "<button type='submit' name='yes'>Yes</button>"
    output += "<button type='submit' name='no'>No</button>"

    output += "</form>"
    output += '</body></html>'
    return output


def restaurant_list():
    output = '<html><body>'
    output += "<a href='/restaurants/new'>Create new restaurant</a>"
    rests = session.query(Restaurant).all()
    if rests:
        output += "<ul>"

    for r in rests:
        output += "<li>%s <a href='/%s/edit'>Edit</a> - <a href='/%s/delete'>Delete</a></li>" \
                  % (r.name, r.id, r.id)

    if rests:
        output += "</ul>"

    output += '</body></html>'
    return output


class webServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            if self.path.endswith('/restaurants'):
                self.wfile.write(restaurant_list())
                return
            elif self.path.endswith('/restaurants/new'):
                self.wfile.write(new_restaurant_form())
                return
            elif self.path.endswith('/delete'):
                rest_id = self.path.split("/")[1]
                rest_id = int(rest_id)
                rest = session.query(Restaurant).filter_by(id=rest_id).one()
                self.wfile.write(delete_restaurant_form(rest_id, rest.name))
                return
            elif self.path.endswith('/edit'):
                rest_id = self.path.split("/")[1]
                rest_id = int(rest_id)
                rest = session.query(Restaurant).filter_by(id=rest_id).one()
                self.wfile.write(edit_restaurant_form(rest_id, rest.name))
                return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            self.send_response(301)
            self.send_header('Location', '/restaurants')
            self.end_headers()

            ctype, pdict = cgi.parse_header(
                self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)

            if self.path.endswith('/restaurants/new'):
                rest_name = fields.get('restaurant_name')

                if rest_name is None or len(rest_name) == 0:
                    raise ValueError("Bad restaurant name")

                create_restaurant(rest_name[0])
                return
            elif self.path.endswith('/edit'):
                rest_id = self.path.split("/")[1]
                rest_id = int(rest_id)
                rest_name = fields.get('restaurant_name')
                update_restaurant(rest_id, rest_name[0])
                return
            elif self.path.endswith('/delete'):
                rest_id = self.path.split("/")[1]
                rest_id = int(rest_id)

                if fields.get('yes'):
                    delete_restaurant(rest_id)
                else:
                    return
        except Exception as e:
            print e


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webServerHandler)
        print "Web Server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()
