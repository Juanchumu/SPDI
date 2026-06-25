FROM nginx:alpine

COPY front-angular/dist/front-angular/browser /usr/share/nginx/html
COPY front-angular/scr/assets/leaflet /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]











