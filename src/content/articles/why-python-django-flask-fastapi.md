---
title: "Why Python? And When to Choose Django, Flask, or FastAPI"
description: "From winning animation contests with Turtle graphics to building production APIs - my journey with Python and the frameworks that power my projects."
pubDate: "Oct 12 2025"
heroImage: "@/assets/python-code.jpg"
heroImageAlt: "Image by suixin390 from Pixabay"
primaryTag: "Python"
tags: ["Django", "Flask", "FastAPI", "Backend"]
---

I won my first programming competition with Python's turtle graphics.

It was a 2-day bootcamp during my bachelor's at MIT Pune - an introduction to learning Python. The bootcamp had various tasks and competitions, and one of them was creating animations. While everyone else was figuring out basic turtle commands, I was making elaborate animations with shapes moving across the screen, colors changing, patterns emerging. I won first place for that animation task.

That's how it started. A graphics library for beginners became my gateway to a language I'd use for the next decade.

## The Ambitious Beginnings

After that bootcamp, I got ambitious. I had already built a Rubik's cube solver in C++ - all logic, no graphics, just print statements showing the moves. My first major Python project was translating that C++ logic to Python and adding 3D graphics using Pygame. Proper rendering, no fancy animations, but I brute-forced almost every move for each square using specific algorithms.

The translation from C++ to Python with graphics? That was a good challenge. Looking back, the code was probably terrible. But it worked, and more importantly, it taught me that Python could do more than draw turtles.

There were many such projects. Each one pushing what I thought Python could do. Then came the final year project - the one that changed everything.

## The Published Project

There were many such projects. Each one pushing what I thought Python could do. Then came the final year project in 2020 - the one that changed everything.

An IoT-based inventory management system with recipe recommendation using collaborative filtering. The objective was to solve a real problem: people have ingredients at home but don't know what to cook, and manually tracking inventory is tedious.

We built four interconnected systems:

**Data Extraction:** Used BeautifulSoup (BS4) and Selenium to scrape approximately 12,000 recipes from various websites. We extracted recipe names, ingredients, cooking instructions, preparation times, and even calculated nutritional values by sending ingredient lists to nutrition websites.

**IoT Inventory Management:** Integrated weight sensors with Raspberry Pi to track ingredient availability in real-time. The data was stored on Firebase Realtime Database, automatically updating as ingredients were used.

**Recipe Recommendation Algorithm:** We developed a recipe scoring algorithm using collaborative filtering. It analyzed user preferences, dietary restrictions, past choices, and - most importantly - what ingredients were actually available in their kitchen right now.

**Android Application:** Built the entire user interface using Python's Kivy library and packaged it as an APK using Buildozer. Users could see personalized recipe recommendations, manage their inventory, and get step-by-step cooking instructions.

The whole system worked together: sensors detect what you have, the algorithm scores thousands of recipes based on your preferences and available ingredients, and the Android app shows you exactly what you can cook right now.

We published this work in Springer: ["IoT Based Inventory Management System with Recipe Recommendation Using Collaborative Filtering"](https://link.springer.com/chapter/10.1007/978-981-15-5258-8_50) and presented it at a conference in Bangalore.

That project taught me something crucial: Python wasn't just good for one thing. It was good for everything I needed to build a complete system. Machine learning algorithms? Python. Web scraping? Python. IoT data processing? Python. Android app? Python with Kivy. All in one language.

## My Language Journey

My programming journey looks like this: C/C++ → Python → JavaScript → Go.

Notice what's missing? Java. I don't like Java, and thankfully it was never in my coursework officially. Some people swear by it. I'm not one of them.

Python stuck because it gave me something the others didn't: **versatility without the ceremony**. I could build anything without fighting the language itself.

## Framework #1: Flask (The Cybage Years)

My introduction to Flask came at Cybage while working on Google projects. They used an internal framework built on top of Flask for static page development. It was my first exposure to web frameworks, and Flask's simplicity made sense.

Flask taught me the fundamentals: routing, templates, request handling. It doesn't force opinions on you. It gives you the basics and lets you build however you want. For static pages and simple web apps, it's perfect.

But as projects grew more complex, I started feeling the limitations. No built-in admin panel. No ORM out of the box. You have to add everything yourself. Which is great for learning, but exhausting for building.

## Framework #2: Django (The Full-Stack Dream)

After Cybage, I wanted to build my own backend system. I'd always been interested in APIs and servers, and I wanted to create a full-stack project for my portfolio - something complete, professional, production-ready.

That's when I chose Django.

Django is the opposite of Flask. It has opinions, lots of them. Built-in admin panel. Powerful ORM. Authentication system. Form handling. Everything you need is already there. You're not building from scratch - you're configuring a system that already works.

For my portfolio backend and later my custom CMS project, Django was the right choice. When you need a complete backend system with a UI, database management, and user authentication, Django saves you weeks of work.

The learning curve is steeper than Flask. The project structure feels heavy when you're used to Flask's simplicity. But once you understand Django's way of doing things, you move incredibly fast.

## Framework #3: FastAPI (The Modern Choice)

Then I discovered FastAPI, and it changed how I think about APIs.

FastAPI is what I reach for at Smart Rewards when I just need API creation - no UI involved. It's easier than Django, less complex, and gives you exactly what you need for building fast, type-safe APIs.

Automatic API documentation. Type hints that actually matter. Async support out of the box. Incredibly fast performance. And all of this with less boilerplate than Django.

I've used all three in many projects now. The choice comes down to what I'm building:

**Use Flask when:** You need something simple and want full control. Small web apps, prototypes, learning projects.

**Use Django when:** You need a complete backend system with UI, admin panel, and database management. CMSs, full-stack applications, anything with complex data models.

**Use FastAPI when:** You just need APIs. Microservices, automation backends, anything where performance matters and you don't need Django's heavyweight features.

## Why Python for Everything

Python's philosophy has always been about readability and simplicity. As Tim Peters wrote in "The Zen of Python"[^1]: *"Simple is better than complex. Complex is better than complicated."* That philosophy shows in everything Python does.

Here's why Python became my default choice and never left:

**Web apps:** Django, Flask, FastAPI - pick your framework based on needs.

**Android apps:** Kivy + Buildozer on Linux. Yes, you can build Android apps with Python.

**Desktop apps:** Tkinter. Not pretty, but functional and ships with Python.

**Games and graphics:** Pygame. From my Rubik's cube project to game interfaces.

**Web scraping:** BeautifulSoup and Selenium. Automate everything.

**Machine learning:** TensorFlow, scikit-learn, PyTorch. The entire ML ecosystem is Python-first.

**Data processing:** Pandas, NumPy. Industry standard for a reason.

**Automation scripts:** Just Python. No framework needed.

One language. All these use cases. That's the Python advantage.

Could I do some of these things in other languages? Sure. JavaScript can build web apps. Go is faster for APIs. Java has Android Studio. But Python lets me do ALL of them without context-switching between languages.

## When I Don't Choose Python

I'm not a Python purist. There are times when Python isn't the right choice.

**When I need raw performance and parallel execution:** Go is my choice. Especially for systems that need to handle thousands of concurrent connections or where execution speed is critical.

At Smart Rewards, if I'm building something that needs to process massive amounts of data in parallel or handle real-time operations at scale, I'd probably reach for Go over Python.

I haven't dived deep into this comparison yet - it's something I'm still exploring. But the general rule is: Python for versatility and development speed, Go for performance and concurrency.

**When I need frontend interactivity:** JavaScript/TypeScript with React. Python can serve the backend, but for rich client-side experiences, JavaScript owns that space.

**When the team already uses something else:** Tools are only as good as the team using them. If everyone knows Java and the codebase is Java, adding Python creates more problems than it solves.

## The Real Decision Framework

Here's how I actually choose what to use:

**Step 1: What am I building?**
- Just APIs → FastAPI
- Full backend with admin → Django
- Simple web app → Flask
- High-performance concurrent system → Go
- ML/Data processing → Python (always)

**Step 2: What does the project need long-term?**
- Will it grow complex? → Django (built for scale)
- Will it stay simple? → Flask (stay lightweight)
- Will performance matter? → FastAPI or Go

**Step 3: Who else will work on this?**
- Just me → Whatever I'm fastest in (usually Python)
- Team project → Match the team's expertise
- Open source → Consider community preferences

## What I've Learned

From turtle graphics to production APIs, Python has been there. Not because it's the "best" at any one thing, but because it's good enough at everything I need it to be.

Django, Flask, and FastAPI aren't competitors - they're tools for different jobs. I've used all three in production. I'll continue using all three because each solves different problems.

The best framework isn't the one with the most GitHub stars or the newest features. It's the one that lets you ship working software without fighting the tools.

And for me, that's usually Python. With whichever framework fits the problem.

---

## References

[^1]: Peters, T. (2004). "The Zen of Python" (PEP 20). Python Enhancement Proposals. Available at: https://peps.python.org/pep-0020/

**Published Work:** Devasthali, A.S., Chaudhari, A.J., Bhutada, S.S., Doshi, S.R., Suryawanshi, V.P. (2021). "IoT Based Inventory Management System with Recipe Recommendation Using Collaborative Filtering." In: Advances in Intelligent Systems and Computing, vol 1053. Springer, Singapore. DOI: 10.1007/978-981-15-5258-8_50