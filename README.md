# Port
### A lightweight blogging platform

`port` makes it easy to run a simple markdown-driven blog. There is no admin UI or database. (no need!)

You use the command-line interface to create a new site, which makes a directory where you can store different folders (folders are treated as categories), and within those folders you write markdown files.

Installation is easy:

    $ pip install port


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

`port` treats any folder in this directory (except for the `.build` and `assets` folders) as a "category".

Within each folder/category, you can write posts as markdown documents (with the `.md` extension).

When you've added or edited documents, you need to re-build the site:

    $ port build my_new_site


## Writing a post

When writing a post, you can include any arbitrary metadata by including a section demarcated by `%~` at the top of your file.

For example:

    %~
    published_at: 6/17/2015 20:45
    draft: true
    %~

This will be parsed and included as part of the `post` object passed to your templates (see below).

You should at least include the `published_at` data; without it `port` will default to using the last build time as the published at value. This can mess up your post ordering.

Other than that, `port` supports [GitHub-Flavored markdown](https://help.github.com/articles/github-flavored-markdown/), so go wild!


## Running a site

To run a site that you've created, just do:

    $ port serve my_new_site

You can optionally specify a port with `--port`.

The main endpoints are:

- `/` - your index page :)
- `/<category name>` - a category index page
- `/<category name>/<post slug>` - a single post
- `/rss` - the rss feed for all your posts (20 most recent published)
- `/rss/<category name>` - the rss feed for one category (20 most recent published)


## Configuration

The new site process will walk you through the basic configuration, which creates a JSON file in the `~/.port` folder. You can edit this JSON file to update your config, or add in arbitrary data which gets passed to your templates as a dictionary called `site_data`.


## Themes

`port` has support for theming - custom themes are super easy to write using [Jinja](http://jinja.pocoo.org/).

#### Templates

New themes go into `~/.port/themes/`. Each theme must, at minimum, include the following templates:

- `category.html` - used to render category pages
- `index.html` - used to render the home page
- `single.html` - used to render single post pages

#### Available data

Within each of these templates, you have access to the following variables:

- `site_data` - a dictionary consisting of the data stored in your site's JSON config file
- post data: `single.html` includes a `post` object, `category.html` and `index.html` include a `posts` list
- pagination data (`category.html` and `index.html`): you get a `page` variable (current page number) and a `last_page` variable (max page number)

`post` objects at minimum consist of:

- `title` - the raw markdown title, extracted from the first `h1` tag
- `title_html` - the compiled title
- `html` - the compiled markdown, not including the title and metadata
- `published_at` - a datetime object
- `category` - the post's category
- `slug` the post's slug
- `draft` - a bool of whether or not the post is a draft

Whatever else you include as metadata in your files will also show up as attributes on the `post` object.

#### Static files

You can refer to static files in your theme at the `/static` url. For instance, if in my new theme I had the file `css/index.css`, I could refer to it at the url `/static/css/index.css`.

#### Example

See the [default theme](https://github.com/ftzeng/port/tree/master/themes/default) for an example.


## Miscellany

- Draft posts are not listed in the category and index pages (and RSS feeds) but can be accessed by their direct url
- Posts are ordered by reverse chron