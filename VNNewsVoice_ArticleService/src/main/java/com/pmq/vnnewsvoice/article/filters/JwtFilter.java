package com.pmq.vnnewsvoice.article.filters;

import com.pmq.vnnewsvoice.article.pojo.CustomUserDetails;
import com.pmq.vnnewsvoice.article.utils.JwtUtils;
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

/**
 * JWT filter for ArticleService — stateless, no DB lookup. Extracts userId and role directly from
 * JWT claims and sets SecurityContext. Public endpoints are not blocked here; Spring Security
 * handles 403/401 for secured ones.
 */
@Component
@RequiredArgsConstructor
public class JwtFilter implements Filter {

  private final JwtUtils jwtUtils;

  @Override
  public void doFilter(
      ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain)
      throws IOException, ServletException {

    HttpServletRequest request = (HttpServletRequest) servletRequest;
    String header = request.getHeader("Authorization");

    if (header != null && header.startsWith("Bearer ")) {
      String token = header.substring(7);
      try {
        if (jwtUtils.validateJwtToken(token)) {
          Long userId = jwtUtils.getUserIdFromJwtToken(token);
          String username = jwtUtils.getUsernameFromJwtToken(token);
          String role = jwtUtils.getRoleFromJwtToken(token);

          if (userId != null && role != null) {
            CustomUserDetails principal =
                new CustomUserDetails(userId, username != null ? username : "", role);
            UsernamePasswordAuthenticationToken auth =
                new UsernamePasswordAuthenticationToken(
                    principal, null, principal.getAuthorities());
            SecurityContextHolder.getContext().setAuthentication(auth);
          }
        }
      } catch (Exception e) {
        // Invalid token — clear context and let Spring Security handle auth requirements
        SecurityContextHolder.clearContext();
      }
    }

    filterChain.doFilter(servletRequest, servletResponse);
  }
}
