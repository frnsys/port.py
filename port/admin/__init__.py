from datetime import datetime
from port.admin import util
from port.admin.auth import requires_auth
from flask import Blueprint, request, render_template, abort, jsonify, url_for


bp = Blueprint('admin',
               __name__,
               url_prefix='/control',
               static_folder='static',
               template_folder='templates')


@bp.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    if request.method == 'GET':
        return render_template('admin/index.html', categories=util.categories())
    elif request.method == 'POST':
        data = request.get_json()
        name = data['category']
        if not name:
            abort(400)
        util.make_category(name)
        return jsonify(success=True)


@bp.route('/<category>', methods=['GET', 'PUT', 'POST'])
@requires_auth
def category(category):
    if request.method == 'GET':
        posts = util.posts_for_category(category)
        cat = util.category_for_slug(category)
        return render_template('admin/category.html', posts=posts, category=cat)

    elif request.method == 'POST':
        data = request.get_json()
        title = data['title']
        if not title:
            abort(400)
        slug = util.slugify(title)
        post = util.single_post(category, slug)
        if post is not None:
            abort(409) # conflict
        else:
            util.write_post(category, slug,
                       published=datetime.now(),
                       draft=True,
                       title=title,
                       body='')
            return jsonify(slug=slug)

    elif request.method == 'PUT':
        # rename category
        data = request.get_json()
        new_slug = util.move_category(category, data['category'])
        return jsonify(slug=new_slug)



@bp.route('/<category>/<slug>', methods=['GET', 'PUT', 'DELETE'])
@requires_auth
def post(category, slug):
    post = util.single_post(category, slug)
    if post is None:
        abort(404)

    if request.method == 'GET':
        return render_template('admin/edit.html', post=post,
                               categories=util.categories())

    elif request.method == 'PUT':
        data = request.get_json()
        title = data['title']

        if not title:
            abort(400)

        slug_ = util.slugify(title)
        cat_ = data['category']

        util.write_post(category, slug,
                   published=datetime.now(),
                   draft=data['draft'],
                   title=data['title'],
                   body=data['body'])

        if util.move_post(category, slug, cat_, slug_):
            return jsonify(success=True, url=url_for('admin.post', category=cat_, slug=slug_))
        else:
            return jsonify(success=True, url=False)

    elif request.method == 'DELETE':
        util.trash_post(category, slug)
        return jsonify(success=True)
