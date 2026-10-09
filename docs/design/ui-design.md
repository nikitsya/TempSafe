# Smart Box: user interface design

## Planned platform

TempSafe will be a responsive web application with a Python/FastAPI backend and an HTML, CSS and JavaScript frontend.
Planned Progressive Web App (PWA) support would let users add a home-screen icon and open the same web application
in a standalone window on supported phones. PWA installation and Web Push require browser/platform testing.
A separate native mobile application is likely to follow the web application, subject to a final team decision.

Home-screen access is a planned enhancement; the browser interface remains the baseline. A web app manifest will
define the application name, icons, start URL and standalone display mode. The proposed Web Push channel will use
a service worker and explicit notification permission. On iOS/iPadOS, Web Push requires the web application to be
added to the home screen. Installation does not make temperature data live while offline.

References: [MDN: Making PWAs installable](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)
and [WebKit: Web Push for Web Apps on iOS and iPadOS](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/).

## Sign-in and access

Users open the HTTPS web application on a phone or desktop browser. Sign-in has labelled login-identifier and password
fields, a Sign in button and a generic failed-login message. Successful sign-in opens the user's assigned prototype box;
an unassigned account sees an explicit no-access message. Sign out invalidates the server session. All box/history
requests are authorised by the backend; hiding a button is not access control.

## Current status concept

![Current status concept from the team presentation](../assets/design/current-status-concept.png)

## History concept

![History concept from the team presentation](../assets/design/history-concept.png)
