FROM amazoncorretto:17-alpine
#openjdk:17-jdk-slim

COPY ./build/libs/CveLabhubBack-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8082
ENTRYPOINT ["java", "-jar", "app.jar"]