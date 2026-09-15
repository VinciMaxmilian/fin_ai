# --- build ------------------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
# As variaveis VITE_* precisam existir no build: o Vite as injeta no bundle.
ARG VITE_API_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ENV VITE_API_URL=$VITE_API_URL \
    VITE_SUPABASE_URL=$VITE_SUPABASE_URL \
    VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY
RUN npm run build

# A CSP precisa saber para onde o app fala. So as ORIGENS entram na diretiva --
# "http://host:8000/api/v1" vira "http://host:8000" -- porque caminho e query
# nao fazem parte de uma origem e invalidariam a regra.
RUN API_ORIGIN=$(printf '%s' "$VITE_API_URL" | sed -E 's#^(https?://[^/]+).*#\1#') \
 && SUPA_ORIGIN=$(printf '%s' "$VITE_SUPABASE_URL" | sed -E 's#^(https?://[^/]+).*#\1#') \
 && SUPA_WS=$(printf '%s' "$SUPA_ORIGIN" | sed -E 's#^https://#wss://#') \
 && printf '%s' \
      "default-src 'self'; \
script-src 'self'; \
style-src 'self' 'unsafe-inline'; \
img-src 'self' data: https:; \
font-src 'self'; \
connect-src 'self' $API_ORIGIN $SUPA_ORIGIN $SUPA_WS; \
frame-ancestors 'none'; frame-src 'none'; object-src 'none'; \
base-uri 'self'; form-action 'self'" > /tmp/csp.txt \
 && echo "CSP gerada: $(cat /tmp/csp.txt)"

# --- runtime ----------------------------------------------------------------
# Imagem "unprivileged": o nginx roda como usuario comum (UID 101), nao root.
# Se um dia alguem escapar do processo, sai sem privilegio no container.
# Ela escuta em 8080 porque portas abaixo de 1024 exigem root.
FROM nginxinc/nginx-unprivileged:1.27-alpine

USER root
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /tmp/csp.txt /tmp/csp.txt

# Injeta a CSP no lugar do marcador e devolve o arquivo ao dono correto.
RUN sed -i "s|__CSP__|$(cat /tmp/csp.txt)|" /etc/nginx/conf.d/default.conf \
 && rm /tmp/csp.txt \
 && chown -R 101:101 /usr/share/nginx/html /etc/nginx/conf.d

USER 101

EXPOSE 8080
