FROM python:3.9.4-alpine3.13

RUN apk add gcc musl-dev

WORKDIR /usr/src/app
COPY scripts/userscripts/pywikibot-scripts/party_colors/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apk del gcc musl-dev

COPY . .

CMD [ "python", "pwb.py", "scripts/userscripts/pywikibot-scripts/party_colors/run.py" ]
