package com.pmq.vnnewsvoice.auth.config;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

@Component
public class RestAccessDeniedHandler implements AccessDeniedHandler {

  @Override
  public void handle(
      HttpServletRequest request,
      HttpServletResponse response,
      AccessDeniedException accessDeniedException)
      throws IOException {
    writeJsonError(response, HttpStatus.FORBIDDEN, "Access denied");
  }

  private void writeJsonError(HttpServletResponse response, HttpStatus status, String message)
      throws IOException {
    response.setStatus(status.value());
    response.setContentType("application/json");
    response.setCharacterEncoding("UTF-8");
    String body =
        String.format(
            "{\"success\":false,\"code\":%d,\"message\":\"%s\",\"result\":null}",
            status.value(), message);
    response.getWriter().write(body);
  }
}
