## Social Media API

![Django](https://img.shields.io/badge/Django-4.2.7-brightgreen.svg)
![Django Rest Framework](https://img.shields.io/badge/Django%20Rest%20Framework-3.14.0-blue.svg)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2.22.0-brightgreen.svg)

Social Media API is a web application built with Django REST Framework offering a platform
for managing and accessing data related to profile interaction, sharing posts and reacting
to them. It provides APIs for various functionalities like creating, listing, searching 
and managing your profile and posts, commenting on posts, reply to comment and react to
posts, comments.

## Features
* Unauthenticated users can see list of posts, profiles, tags
* For authenticated users opens - reacting to posts/comments (like/dislike) see comments 
  under posts and replies under comments, creating posts, comments, replies.
* * Superuser (admin, staff) have admin site http://localhost:8000/admin/ with full control
* When user register, backend creates profile using signals
* For Authentication system we are using REST framework token authentication system
* User can reset password via email
* Users can filter profiles by username and posts by tag url in every post response
* API documentation  http://127.0.0.1:8000/api/doc/swagger/
* Admin panel  http://localhost:8000/admin/

## Installation
1. Clone git repository to your local machine:
```
    git clone https://github.com/OlehOryshchuk/social_media_api
```
2. Copy the `.env.sample` file to `.env` and configure the environment variables
```
    cp .env.sample .env
```
3. Run command. Docker should be installed:
```
    docker-compose up --build
```
4. Access API as superuser you can use the following admin user account:

- **Username** CoolGuy
- **Email** social_admin@gmail.com : Email is not valid
- **Password** rvyalas23

It is recommended to create your own user account with real email, so you could
use reset password via email and for production use.

### Usage
To access the API, navigate to http://localhost:8000/api/ in your web browser and enter one of endpoints.

### Endpoints
Social Media API endpoints 

prf_id - is the profile integer id
- `/social_media/` - default basic root
- `/social_media/profiles/` - see list of profiles
- `/social_media/profiles/prf_id/` - Detail page of profile where owner can manage profile.
- `/social_media/profiles//followings/` - see profile followings
- `/social_media/profiles/prf_id/followers/` - see profile followers
- `/social_media/profiles/prf_id/follow_or_unfollow/` - follow/unfollow profile
- `/social_media/profiles/prf_id/upload_profile_picture/` - upload profile picture
- `/social_media/posts/prf_id/profile/` - see profile posts

post_id - is the post integer id 
- `/social_media/posts/` - see list of posts/create profile
- `/social_media/posts/post_id/` - Detail page of post where owner can manage post.
- `/social_media/posts/post_id/like/` - Like post or unlike
- `/social_media/posts/post_id/dislike/` - Dislike post or remove dislike
- `/social_media/post/post_id/comments/` - See post comments filtered by number of 
   most likes and number of replies, least number of dislikes. And also create comment or reply 

cmt_id - is comment integer id

- `/social_media/post/comments/cmt_id/replies/` - see all replies under comment

And all comments and replies we can filter in descending or ascending order
by comment creating time

User API endpoints:
- `/user/` - register user
- `/user/me/` - manage user
- `/user/auth/token/login/` - login
- `/user/auth/token/logout/` - logout
- `/user/set_password/` - set new user password
- `/user/set_email/` - set new email
- `/user/reset_password/` - reset password via email
- `/user/password-reset-confirm/uidb64/token/` -  uidb = User id &
    token - temporary token. I created frontend part just for the sake of
    using reset password feature.

All the user endpoints provides djoser package which provide much more
endpoints. To see all available endpoints see in https://djoser.readthedocs.io/en/latest/getting_started.html#available-endpoints.
But the above endpoints are the mains.

Admin (superuser) endpoint:
- `/admin/`

Documentation:
- `/doc/swagger/`: To access the API documentation, you can visit the interactive Swagger UI.
