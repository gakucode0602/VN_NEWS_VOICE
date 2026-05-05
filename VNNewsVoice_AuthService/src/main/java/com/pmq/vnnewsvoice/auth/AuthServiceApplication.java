package com.pmq.vnnewsvoice.auth;

import io.github.cdimascio.dotenv.Dotenv;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class AuthServiceApplication {

  public static void main(String[] args) {
    Dotenv dotenv = Dotenv.configure().ignoreIfMissing().load();
    dotenv.entries().forEach(e -> System.setProperty(e.getKey(), e.getValue()));
    SpringApplication.run(AuthServiceApplication.class, args);
  }
}
