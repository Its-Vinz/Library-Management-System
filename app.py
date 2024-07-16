from crypt import methods
from flask import Flask, jsonify, render_template, request, url_for, redirect, flash, session, make_response
from networkx import is_connected
from sqlalchemy import true
from dotenv import load_dotenv
import functools, string, mysql.connector, os

app = Flask(__name__)
load_dotenv(dotenv_path="credit.env")
app.secret_key = os.getenv("SECRET_KEY")

con = None
cur = None

def db_connection():
    global con
    if not con or not con.is_connected():
        con = mysql.connector.connect(
                                    	host = os.getenv('DATABASE_HOST'),
                                    	user = os.getenv('DATABASE_USER'),
                                    	passwd = os.getenv('DATABASE_PASSWORD'),
                                    	database = os.getenv('DATABASE_NAME'))
    return con

'''

  //  nocache function 

'''

def nocache(view):
    @functools.wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
        return response
    return no_cache


'''

  //  Home, Login, Create-Account, Logout function routes

'''

@app.route('/')
@nocache
def index():
    return render_template('index.html')


@app.route('/login',methods=['GET','POST'])   
@nocache
def login():
    if request.method == 'POST':
        user = request.form['username']
        password = request.form['password']
        utype = request.form['utype']

        try:
            con = db_connection()
            cur = con.cursor()
            query = ("SELECT Name FROM USER WHERE Uname=%s AND Upass=%s AND Utype=%s AND Ustatus=%s;")
            data = (user,password,utype,"approved")
            cur.execute(query,data)
            result = cur.fetchone()

            if result:
                flash('login successfull!','success')
                session['user_name'] = result[0] # type: ignore
                session['user_type'] = utype
                if utype == 'admin':
                    return redirect(url_for('AdminDashboard'))
                else:
                    return redirect(url_for('UserDashboard'))
            else:
                flash('Invalid username or password','danger')

        except mysql.connector.Error as e:
            flash(f'Database Error: {e}','danger')
        except Exception as e:
            flash(f'Exception Pointed: {e}','danger')
        finally:
            if con and con.is_connected and cur:
                cur.close()
                con.close()

    return render_template('login.html')


@app.route('/createAccount',methods=['GET','POST'])
@nocache
def createAccount():
    if request.method == "POST":
        NameUser = request.form['name']
        User_name = request.form['username']
        Password = request.form['password']
        User_type = request.form['utype']

        if not NameUser or not User_name or not Password or not User_type:
            flash('All fileds are required','danger')
            return redirect(url_for('createAccount'))

        try:
            con = db_connection()
            cur = con.cursor()
            query = ("INSERT INTO USER(Name,Uname,Upass,Utype) VALUES(%s,%s,%s,%s)")
            data = (NameUser,User_name,Password,User_type)
            cur.execute(query,data)
            con.commit()

            if NameUser and User_name and Password and User_type:
                flash('Account Created Successfully! your account request is in under review, login after 30 minutes','success')
                return redirect(url_for('index'))
            else:
                flash('Failed to create account!','danger')
                return redirect(url_for('index'))

        except mysql.connector.Error as e:
            flash(f'Database Error: {e}','danger')
        except Exception as e:
            flash(f'Excpetion Pointed: {e}','danger')

            return redirect(url_for('index'))
        finally:
            if con and con.is_connected and cur:
                cur.close()
                con.close()

    return render_template('createAccount.html')


@app.route('/logout')                       
@nocache
def logout():
    session.clear()
    flash('You have been logged out','success')
    return redirect(url_for('login'))



'''

  //  User and Admin Dashboard route 

'''

@app.route('/AdminDashboard')
@nocache
def AdminDashboard():
    if 'user_name' not in session or 'user_type' not in session:
        flash('You are not logged in!','danger')
        return redirect(url_for('login')) 
    user_name = session['user_name']
    user_type = session['user_type']

    return render_template('AdminDashboard.html',user_name=user_name,user_type=user_type)


@app.route('/UserDashboard')
@nocache
def UserDashboard():
    if 'user_name' not in session or 'user_type' not in session:
        flash('you are not logged in!','danger')
        return redirect(url_for('login'))
    user_name = session['user_name']
    user_type = session['user_type']

    return render_template('UserDashboard.html',user_name=user_name,user_type=user_type)



'''

  //  Display, Add, Search, Sort, Update operations route   // starts here 

'''

@app.route('/displayRecord')
# @nocache
def displayRecord():
    try: 
        con = db_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM BOOK")
        records = cur.fetchall()

    except mysql.connector.Error as e:
        flash(f'Database Error: {e}','danger')
    except Exception as e:
        flash(f'Exception Pointed: {e}','danger')

        return redirect(url_for('AdminDashboard'))
    finally:
        if con and con.is_connected and cur:
            cur.close()
            con.close()

    return render_template('displayRecord.html',records=records)


@app.route('/addRecord',methods=['GET','POST'])
# @nocache
def addRecord():
    if request.method == 'POST':
        BOOKNAME = request.form['bookName']
        BOOKAUTHOR = request.form['bookAuthor']
        BOOKPUBLICATION = request.form['bookPublication']
        BOOKQUANTITY = request.form['bookQuantity']
        BOOKPRICE = request.form['bookPrice']

        if not BOOKNAME or not BOOKAUTHOR or not BOOKPUBLICATION or not BOOKQUANTITY or not BOOKPRICE:
            flash('All fields are required!', 'danger')
            return redirect(url_for('AdminDashboard'))

        try:
            BOOKQUANTITY = int(BOOKQUANTITY)
            BOOKPRICE = float(BOOKPRICE)
            BOOKTOTAL = BOOKQUANTITY * BOOKPRICE 

            con = db_connection()
            cur = con.cursor()
            query = ("INSERT INTO BOOK (Bname,Bauth,Bpub,Bqty,Bprice,Total) VALUES(%s,%s,%s,%s,%s,%s)")
            data = (BOOKNAME,BOOKAUTHOR,BOOKPUBLICATION,BOOKQUANTITY,BOOKPRICE,BOOKTOTAL)
            cur.execute(query,data)
            con.commit()

            flash('Record added successfully!', 'success')
            return redirect(url_for('AdminDashboard'))

        except mysql.connector.Error as e:
            flash(f'Database Error: {e}','danger')
        except Exception as e:
            flash(f'Exception Pointed: {e}','danger')

            return redirect(url_for('AdminDashboard'))
        finally:
            if con and con.is_connected and cur:
                cur.close()
                con.close()

    return render_template('addRecord.html')


@app.route('/deleteRecord',methods=['GET','POST'])
# @nocache
def deleteRecord():
    records = []
    try:
        con = db_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM BOOK")
        records = cur.fetchall()

    except mysql.connector.Error as e:
        flash(f'Database Error: {e}', 'danger')
    except Exception as e:
        flash(f'Exception Pointed: {e}', 'danger')

        return redirect(url_for('AdminDashboard'))
    finally:
        if con and con.is_connected and cur:
            cur.close()
            con.close()

    if request.method == 'POST':
        serial = request.form['serialNo']

        try:
            con = db_connection()
            cur = con.cursor()
            query = "DELETE FROM BOOK WHERE Bid=%s;"
            cur.execute(query, (serial,))
            con.commit()

            if cur.rowcount > 0:
                flash('Record deleted successfully!', 'success')
            else:
                flash('Failed to delete record!', 'danger')

            return redirect(url_for('deleteRecord'))

        except mysql.connector.Error as e:
            flash(f'Database Error: {e}', 'danger')
        except Exception as e:
            flash(f'Exception Pointed: {e}', 'danger')

            return redirect(url_for('AdminDashboard'))
        finally:
            if con and con.is_connected and cur: 
                cur.close()
                con.close()

    return render_template('deleteRecord.html', records=records)


@app.route('/updateRecord',methods=['GET','POST'])
# @nocache
def updateRecord():
    if request.method == 'POST':
        serialno = request.form['serialNo']
        BOOKNAME = request.form['bookName']
        BOOKAUTHOR = request.form['bookAuthor']
        BOOKPUBLICATION = request.form['bookPublication']
        BOOKQUANTITY = request.form['bookQuantity']
        BOOKPRICE = request.form['bookPrice']

        if not serialno or not BOOKNAME or not BOOKAUTHOR or not BOOKPUBLICATION or not BOOKQUANTITY or not BOOKPRICE:
            flash('All fields are required!', 'danger')
            return redirect(url_for('AdminDashboard'))

        try:
            BOOKQUANTITY = int(BOOKQUANTITY)
            BOOKPRICE = float(BOOKPRICE)
            BOOKTOTAL = BOOKQUANTITY * BOOKPRICE

            con = db_connection()
            cur = con.cursor()
            query = ("UPDATE BOOK SET Bname=%s, Bauth=%s, Bpub=%s, Bqty=%s, Bprice=%s, Total=%s WHERE Bid=%s;")
            data = (BOOKNAME,BOOKAUTHOR,BOOKPUBLICATION,BOOKQUANTITY,BOOKPRICE,BOOKTOTAL,serialno)
            cur.execute(query,data)
            con.commit()

            if cur.rowcount > 0:
                flash('Record updated successfully','success')
            else:
                flash('Record not found!','danger')
                return redirect(url_for('AdminDashboard'))            

        except mysql.connector.Error as e:
            flash(f'Database Error: {e}','danger')
        except Exception as e:
            flash(f'Exception Pointed: {e}','danger')

            return redirect(url_for('AdminDashboard'))
        finally:
            if con and con.is_connected and cur:
                cur.close()
                con.close()

    return render_template('updateRecord.html')


@app.route('/searchRecord',methods=['GET','POST'])
def searchRecord():
    records = []
    if request.method == 'POST':
        searchBy = request.form['searchBy']
        searchValue = request.form['searchValue']

        try:
            con = db_connection()
            cur = con.cursor()
            query = ""

            if searchBy == "serialno":
                query = "SELECT * FROM BOOK WHERE Bid = %s"
            elif searchBy == "name":
                query = "SELECT * FROM BOOK WHERE Bname = %s"
            elif searchBy == "author" :
                query = "SELECT * FROM BOOK WHERE Bauth = %s"
            elif searchBy == "publication":
                query = "SELECT * FROM BOOK WHERE Bpub = %s"
            else:
                query = None

            if query:
                cur.execute(query, (searchValue,))
                records = cur.fetchall()
            else:
                flash('Invalid search parameter', 'danger')

        except mysql.connector.Error as e:
            flash(f'Database Error: {e}','danger')
        except Exception as e:
            flash(f'Exception Pointed: {e}','danger')
        finally:
            if con and con.is_connected and cur:
                cur.close()
                con.close()

    return render_template('searchRecord.html',records=records)


@app.route('/sortRecord',methods=['GET','POST'])
@nocache
def sortRecord():
    records = []
    if request.method == 'POST':
        sortBy = request.form['sortBy']
        sortValue = request.form['sortValue']

        try:
            con = db_connection()
            cur = con.cursor()
            query = ""

            if sortBy == "serialno":
                query = "SELECT * FROM BOOK ORDER BY Bid ASC"
            elif sortBy == "name":
                query = "SELECT * FROM BOOK ORDER BY Bname ASC"
            elif sortBy == "author":
                query = "SELECT * FROM BOOK ORDER BY Bauth ASC"
            elif sortBy == "publication":
                query = "SELECT * FROM BOOK ORDER BY Bpub ASC"
            if sortBy == "serialnoDES":
                query = "SELECT * FROM BOOK ORDER BY Bid DESC"
            elif sortBy == "nameDES":
                query = "SELECT * FROM BOOK ORDER BY Bname DESC"
            elif sortBy == "authorDES":
                query = "SELECT * FROM BOOK ORDER BY Bauth DESC"
            elif sortBy == "publicationDES":
                query = "SELECT * FROM BOOK ORDER BY Bpub DESC"

            cur.execute(query)
            records = cur.fetchall()

        except mysql.connector.Error as e:
            flash(f'Database Error: {e}','danger')
        except Exception as e:
            flash(f'Exception Pointed: {e}','danger')
        finally:
            if con and con.is_connected and cur: 
                cur.close()
                con.close()

    return render_template('sortRecord.html',records=records)


@app.route('/resetPassword', methods=['GET', 'POST'])
def resetPassword():
    if request.method == 'POST':
        username = request.form['username']
        passwd = request.form['passwd']

        try:
            con = db_connection()
            cur = con.cursor()
            cur.execute("SELECT Upass FROM USER WHERE Uname = %s", (username,))
            existing_password = cur.fetchone()

            if not existing_password:
                flash('Username not found!', 'danger')
            elif existing_password and existing_password[0] == passwd:
                flash('New password is the same as the existing one!', 'danger')
            else:
                query = "UPDATE USER SET Upass = %s WHERE Uname = %s"
                data = (passwd, username)
                cur.execute(query, data)
                con.commit()
                flash('Password updated!', 'success')

        except mysql.connector.Error as e:
            flash(f'Database Error: {e}', 'danger')
        except Exception as e:
            flash(f'Exception occurred: {e}', 'danger')
        finally:
            if con and con.is_connected and con:
                cur.close()
                con.close()

        return redirect(url_for('resetPassword'))

    return render_template('resetPassword.html')


@app.route('/checkUsername', methods=['POST'])
def checkUsername():
    username = request.form['username']
    exists = False

    try:
        con = db_connection()
        cur = con.cursor()
        cur.execute("SELECT 1 FROM USER WHERE Uname = %s", (username,))
        if cur.fetchone():
            exists = True

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if con and con.is_connected and cur:
            cur.close()
            con.close()

    return jsonify({"exists": exists})


@app.route('/approvalPanel')
def approvalPanel():
    return render_template('approvalPanel.html')


@app.route('/displayUsers')
def displayUsers():
    records = []
    try: 
        con = db_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM USER;")
        records = cur.fetchall()

    except mysql.connector.Error as e:
        flash(f'Database Error: {e}','danger')
    except Exception as e:
        flash(f'Exception Pointed: {e}','danger')

        return redirect(url_for('AdminDashboard'))
    finally:
        if con and con.is_connected and cur:
            cur.close()
            con.close()

    return render_template('displayUsers.html',records=records)


@app.route('/deleteUsers',methods=['GET','POST'])
# @nocache
def deleteUsers():
    records = []
    try:
        con = db_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM USER")
        records = cur.fetchall()

    except mysql.connector.Error as e:
        flash(f'Database Error: {e}', 'danger')
    except Exception as e:
        flash(f'Exception Pointed: {e}', 'danger')

        return redirect(url_for('AdminDashboard'))
    finally:
        if con and con.is_connected and cur:
            cur.close()
            con.close()

    if request.method == 'POST':
        serial = request.form['serialNo']

        try:
            con = db_connection()
            cur = con.cursor()
            query = "DELETE FROM USER WHERE Uid=%s;"
            cur.execute(query, (serial,))
            con.commit()

            if cur.rowcount > 0:
                flash('User removed!', 'success')
            else:
                flash('Failed to delete record!', 'danger')

            return redirect(url_for('deleteUsers'))

        except mysql.connector.Error as e:
            flash(f'Database Error: {e}', 'danger')
        except Exception as e:
            flash(f'Exception Pointed: {e}', 'danger')

            return redirect(url_for('AdminDashboard'))
        finally:
            if con and con.is_connected and cur:
                cur.close()
                con.close()

    return render_template('deleteUsers.html', records=records)


@app.route('/updateUser',methods=['GET','POST'])
@nocache
def updateUser():
    try:
        con = db_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM USER;")
        records = cur.fetchall()

    except mysql.connector.Error as e:
        flash(f'Database Error: {e}','danger')
    except Exception as e:
        flash(f'Exception Pointed: {e}','danger')

        return redirect(url_for('AdminDashboard'))
    finally:
        if con and con.is_connected and cur:
            cur.close()
            con.close()

    if request.method == 'POST':
        serialno = request.form['serialno']

        try:
            con = db_connection()
            cur = con.cursor()
            query = ("UPDATE USER SET Ustatus = %s WHERE Uid = %s;")
            data = ("Approved",serialno)
            cur.execute(query,data)
            con.commit()

            if cur.rowcount == 0:
                flash('No user found!','danger')
            else:
                flash('User Approved!','success')
                return redirect(url_for('updateUser'))

            
        except mysql.connector.Error as e:
            flash(f'Database Error: {e}','danger')
        except Exception as e:
            flash(f'Exception Pointed: {e}','danger')

            return redirect(url_for('AdminDashboard'))
        finally:
            if con and con.is_connected and cur:
                cur.close()
                con.close()

    return render_template('updateUser.html',records=records)


if __name__ == '__main__':
    app.run(debug=True)