# Port
### A lightweight blogging platform

`port` makes it easy to run a simple markdown-driven blog/static site generator. There is no admin UI or database. (no need!)

You use the command-line interface to create a new site, which makes a directory where you can store different folders (folders are treated as categories), and within those folders you write markdown files.

Installation is easy:

    $ pip install port

(`port` requires Python 3)

## Example

An example site is my own blog: [space and times](http://spaceandtim.es/)

## Features

- Supports **GitHub-Flavored** Markdown
- Supports **MathJax** syntax (in the default theme)
- Includes **RSS feeds** for each category and all posts


## Creating a site

To create a site, use the `port` command-line tool:

    $ port create my_new_site

You will be walked through the basic configuration.

A folder will created at whatever directory you specified during configuration.

In there you will notice three folders:

- `.build` - this is where your compiled posts are stored. This folder is destroyed every build, so don't store anything important there.
- `assets` - this is where your static files will be served from. So for example you could place `my_image.png` in this folder and then in your posts you could refer to `/assets/my_image.png`.
- `default_category` - this is the default category folder. You can rename this or replace it.
- `pages` - this is where you can put non-post/non-category pages, also as markdown. For example, an "About" page.

`port` treats any folder in this directory (except for the `.build`, `assets`, and `pages` folders) as a "category".

Within each folder/category, including the `pages` folder, you can write posts as markdown documents (with the `.md` extension).

When you've added or edited documents, you need to re-build the site:

    $ port build my_new_site


## Writing a post

When writing a post, you can include any arbitrary metadata using YAML front matter, i.e. by including a section demarcated by `---` at the very top of your file.

For example:

    ---
    published_at: 6/17/2015 20:45
    draft: true
    ---

This will be parsed and included as part of the `post` object passed to your templates (see below).

You should at least include the `published_at` data; without it `port` will default to using the last build time as the published at value. This can mess up your post ordering.

Other than that, `port` supports [GitHub-Flavored markdown](https://help.github.com/articles/github-flavored-markdown/), so go wild!

Pages are written exactly the same as posts - in Markdown and with optional YAML front matter as well.


## Running a site

To preview the site, you can run:

    port serve my_new_site -p 8080

This will auto-rebuild the site when files change.

The main endpoints are:

- `/` - your index page :)
- `/<category name>` - a category index page
- `/<category name>/<post slug>` - a single post
- `/rss` - the rss feed for all your posts (20 most recent published)
- `/rss/<category name>` - the rss feed for one category (20 most recent published)
- `/<page>` - a non-post/non-category page


## Configuration

The new site process will walk you through the basic configuration, which creates a yaml file in the `~/.port` folder. You can edit this yaml file to update your config, or add in arbitrary data which gets passed to your templates as a dictionary called `site_data`.

## Miscellany

- Draft posts are not listed in the category and index pages (and RSS feeds) but can be accessed by their direct url
- Posts are ordered by reverse chron
- Arbitrary category metadata can be added for each category by creating a `meta.yaml` file in the category's directory. You can override the template used for a category here and/or the posts per page value, e.g.:

```
template: a_special_template.html
per_page: 20
```

- Pages can similarly have a different template specified in their YAML front matter.

---

## Themes

`port` has support for theming - custom themes are super easy to write using [Jinja](http://jinja.pocoo.org/).

#### Templates

New themes go into `~/.port/themes/`. Each theme must, at minimum, include the following templates:

- `category.html` - used to render category pages
- `index.html` - used to render the home page
- `single.html` - used to render single post pages
- `page.html` - used to render non-post/non-category pages
- `404.html` - 404 error page

#### Available data

Within each of these templates, you have access to the following variables:

- `site_data` - an object consisting of the data stored in your site's yaml config file and additional metadata, such as `categories`. Note that the attribute names corresponding to keys in your site's config are lowercase (e.g. if you have `SITE_NAME` in your config, it is accessed at `site_data.site_name`)
- post data: `single.html` includes a `post` object, `category.html` and `index.html` include a `posts` list
- pagination data (`category.html` and `index.html`): you get a `page` object which includes `page.current`, `page.next` (the next page's url, `None` if there is no next page), and `page.prev`

`post` objects at minimum consist of:

- `title` - the raw markdown title, extracted from the first `h1` tag
- `title_html` - the compiled title
- `html` - the compiled markdown, not including the title and metadata
- `published_at` - a datetime object
- `category` - the post's category
- `slug` the post's slug
- `draft` - a bool of whether or not the post is a draft

Whatever else you include as metadata in your files will also show up as attributes on the `post` object.

`page` objects are similar, at minimum consisting of:

- `title` - the raw markdown title, extracted from the first `h1` tag
- `title_html` - the compiled title
- `html` - the compiled markdown, not including the title and metadata
- `slug` the post's slug
- `draft` - a bool of whether or not the post is a draft

#### JS & CSS

The theme's JS and CSS folders are available at `/js` and `/css` respectively.

#### Example

See the [default theme](https://github.com/frnsys/port/tree/master/port/themes/default) for an example.

---

#### Syncing to a remote folder

I work on my posts on my local machine, and when they are ready, I build them and then sync the local folder to my remote server which hosts the live site.

There's a convenience command for doing this:

    $ port sync <site name> <remote>

For example:

    $ port sync my_new_site user@mysite.com:~/my_site

---

## Pro tips

- If you're using vim, you can configure a keybinding to drop in the current datetime for you, which is useful for setting the `published_at` value in a post's yaml frontmatter, e.g.:

```
nnoremap <leader>, "=strftime("%m.%d.%Y %H:%M")<CR>P
```

- Example nginx conf:

```
server {
    listen      80;
    server_name my.site.co;
    root        /srv/my_new_site;
    error_page  404     /404.html;
}
```
