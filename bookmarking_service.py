
import flask
from flask import jsonify
from flask import request
import sqlite3
import json

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/bookmarking/users', methods=['GET'])
def user():
    conn = sqlite3.connect('bookmarks.db')
    cur = conn.cursor()
    cur.execute('SELECT user_id, user_name FROM Users ORDER BY user_id ASC;')
    users = []
    for row in cur.fetchall():
        users.append({
            "user_id": row[0],
            "user_name": row[1]
        })
    result = {
        "count": str(len(users)),
        "users": users
    }
    return jsonify(result),200


@app.route('/bookmarking', methods=['POST'])
def add_user():
    try:
        add_user = json.loads(request.data)
        conn = sqlite3.connect("bookmarks.db")
        cur = conn.cursor()
        for row in add_user:
            cur.execute('SELECT COUNT(*) FROM Users WHERE user_id = ? OR user_name = ?;', (row["user_id"], row["user_name"]))
            match = cur.fetchone()[0]
            if match > 0:
                return jsonify({
                    "resons": [
                        {
                            "message": "One/more of the user(s) exists already"
                        }
                    ]
                }), 400
        for row in add_user:
            cur.execute('INSERT INTO Users(user_id, user_name) VALUES(?,?);', (row["user_id"], row["user_name"]))
            conn.commit()
        conn.close()
        return jsonify(add_user), 201
    except :
        return jsonify({
            "Internal Server Error:"
        }), 500


@app.route('/bookmarking/<user_id>', methods=['DELETE'])
def remove_user(user_id):
    conn = sqlite3.connect("bookmarks.db")
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM Users WHERE user_id = ?;', (user_id,))
    if cur.fetchone()[0] == 0:
        return jsonify({
            "resons": [
                {
                    "message": "User not found"
                }
            ]
        }), 404
    cur.execute('DELETE FROM Bookmarks WHERE Bookmarks.user_id = ?;', (user_id,))
    conn.commit()

    cur.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))
    conn.commit()

    conn.close()
    return "Deleted", 204

@app.route('/bookmarking/bookmarks', methods=['GET'])
def show_bookmarks():
    conn = sqlite3.connect("bookmarks.db")
    cur = conn.cursor()
    query_parameters = request.args
    tags = query_parameters.get('tags')
    count = query_parameters.get('count')
    offset = query_parameters.get('offset')

    sql = "SELECT url, tags, text, user_id FROM Bookmarks "
    if tags:
        sql += "WHERE tags LIKE '%" + str(tags)+ "%' "
    sql += "ORDER BY url "
    if count:
        sql += "LIMIT " + str(count) + " "
    if offset:
        sql += "OFFSET " + str(offset)

    cur.execute(sql)
    bookmarks = []
    for row in cur.fetchall():
        bookmarks.append({
            "url": row[0],
            "tags": row[1],
            "text": row[2],
            "user_id": row[3]

        })
    result = {
        "count": str(len(bookmarks)),
        "bookmarks": bookmarks
    }

    conn.close()
    return jsonify(result), 200

@app.route('/bookmarking/bookmarks/<user_id>', methods=['GET'])
def show_user_bookmarks(user_id):

    conn = sqlite3.connect("bookmarks.db")
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM Users WHERE user_id = ?;', (user_id,))
    if  cur.fetchone()[0] == 0:
        return jsonify({
            "resons": [
                {
                    "message": "User not found"
                }
            ]
        }), 404

    sql = "SELECT url, tags, text, user_id FROM Bookmarks WHERE user_id = '" + user_id + "';"
    query_parameters = request.args
    tags = query_parameters.get('tags')
    count = query_parameters.get('count')
    offset = query_parameters.get('offset')
    if tags:
        sql += "WHERE tags LIKE '%" + str(tags)+ "%' "
    if count:
         sql += "LIMIT " + str(count)
    if offset:
        sql += "OFFSET " + str(offset)

    cur.execute(sql)
    bookmarks = []
    for row in cur.fetchall():
        bookmarks.append({
            "url": row[0],
            "tags": row[1],
            "text": row[2],
            "user_id": row[3]
        })
    result = {
        "count": str(len(bookmarks)),
        "bookmarks": bookmarks
    }
    conn.close()
    return jsonify(result), 200

@app.route('/bookmarking/bookmarks/<user_id>/<path:url>', methods=['GET'])
def get_user_bookmarks_by_url(user_id,url):
    conn = sqlite3.connect("bookmarks.db")
    cur = conn.cursor()
    cur.execute( 'SELECT url, tags, text, user_id FROM Bookmarks WHERE user_id = ? AND url = ?;',(user_id,url))
    bookmarks = []
    for row in cur.fetchall():
        bookmarks.append({
            "url": row[0],
            "tags": row[1],
            "text": row[2],
            "user_id": row[3]
        })
    result = {
        "count": str(len(bookmarks)),
        "bookmarks": bookmarks
    }
    conn.close()
    return jsonify(result), 200

@app.route('/bookmarking/<user_id>/bookmarks', methods=['POST'])
def add_bookmarks(user_id):

    try:
        add = json.loads(request.data)
        bookmarks = add["bookmarks"]
        conn = sqlite3.connect("bookmarks.db")
        cur = conn.cursor()

        cur.execute('SELECT COUNT(*) FROM Users WHERE user_id = ?;', (user_id,))
        if cur.fetchone()[0] != 1:
            return jsonify({
                "resons": [
                    {
                        "message": "User not found"
                    }
                ]
            }), 404

        for row in bookmarks:
            cur.execute('SELECT COUNT(*) FROM Bookmarks WHERE user_id = ? ;', (user_id,))
            if cur.fetchone()[0] > 0:
                return jsonify({
                    "resons": [
                        {
                            "message": "Bookmark " + bookmark['url'] + " already exists"
                        }
                    ]
                }), 400

        for row in bookmarks:
            cur.execute('INSERT INTO Bookmarks(url, tags, text, user_id) VALUES(?,?,?,?);', (row["url"], row["tags"], row["text"], row["user_id"]))
            conn.commit()

        conn.close()
        return jsonify(add), 201
    except:
        return jsonify({
            "Internal Server Error"
        }), 500



@app.route('/bookmarking/<user_id>/bookmarks/<path:url>', methods=['PUT'])
def update_bookarmks(user_id, url):
    try:
        update = json.loads(request.data)
        bookmarks = update["bookmarks"]
        conn = sqlite3.connect("bookmarks.db")
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM Users WHERE user_id = ?;', (user_id,))
        if cur.fetchall()[0] == 0:
            return jsonify({
                "resons":[
                    {
                        "message": "User not found"
                    }
                ]
            }),404

        for row in bookmarks:
            cur.execute('SELECT COUNT(*) FROM Bookmarks WHERE user_id = ? AND url = ?;',(user_id,url))
            if cur.fetchall()[0] == 0:
                return jsonify({
                    "resons":[
                        {
                            "message": "Bookmark does not exists"
                        }
                    ]
                }),404
        for row in bookmarks:
            cur.execute('UPDATE Bookmarks SET tags = ?, text = ?, user_id = ? WHERE user_id = ? AND url = ?;',(row["tags"],row["text"],row["user_id"],row["user_id"],row["url"]))
            conn.commit()
        conn.close()
        return jsonify(update),201
    except :
        return jsonify({
            "Internal Server Error"
        }), 500


@app.route('/bookmarking/<user_id>/bookmarks/<path:url>', methods=['DELETE'])
def delete_bookmarks(user_id, url):
    try:
        conn = sqlite3.connect("bookmarks.db")
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM Users WHERE user_id = ?;', (user_id,))
        if cur.fetchone()[0] != 1:
            return jsonify({
                "resons": [
                    {
                        "message": "User not found"
                    }
                ]
            }), 404

        cur.execute('SELECT COUNT(*) FROM Bookmarks WHERE user_id = ? AND url = ?;', (user_id,url))
        if cur.fetchone()[0] == 0:
            return jsonify({
                "resons": [
                    {
                        "message": "Bookmark not found"
                    }
                ]
            }), 404

        cur.execute('DELETE FROM Bookmarks WHERE user_id = ? AND url = ?', (user_id,url))
        conn.commit()
        conn.close()
        return "Deleted", 204
    except:
        return jsonify({
            "error"
        }), 500
app.run()
