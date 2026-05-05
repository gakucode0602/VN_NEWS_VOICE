# syntax=docker/dockerfile:1.7
FROM eclipse-temurin:21-jdk-jammy AS build

WORKDIR /workspace

COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
RUN chmod +x mvnw

COPY src/ src/
RUN ./mvnw -B -DskipTests clean package
RUN JAR_FILE="$(find target -maxdepth 1 -type f -name '*.jar' ! -name '*original*.jar' | head -n 1)" \
    && test -n "$JAR_FILE" \
    && cp "$JAR_FILE" target/app.jar

FROM eclipse-temurin:21-jre-jammy

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY --from=build /workspace/target/app.jar /app/app.jar

EXPOSE 8084

USER appuser

ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar /app/app.jar"]
