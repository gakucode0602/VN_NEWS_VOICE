package com.pmq.vnnewsvoice.auth.controller;

import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.NotificationDto;
import com.pmq.vnnewsvoice.auth.facade.ApiNotificationFacade;
import com.pmq.vnnewsvoice.auth.pojo.CustomUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/notifications")
@PreAuthorize("isAuthenticated()")
public class ApiNotificationController {
  private final ApiNotificationFacade apiNotificationFacade;

  @PostMapping("/{id}/read")
  public ResponseEntity<NotificationDto> markAsRead(
      @PathVariable Long id, @AuthenticationPrincipal CustomUserDetails principal) {
    ApiResult<NotificationDto> result = apiNotificationFacade.markAsRead(id, principal);
    if (result.getStatus() == HttpStatus.NOT_FOUND) {
      return ResponseEntity.notFound().build();
    }
    return ResponseEntity.status(result.getStatus()).body(result.getResult());
  }

  @PostMapping("/mark-all-read")
  public ResponseEntity<Void> markAllAsRead(@AuthenticationPrincipal CustomUserDetails principal) {
    ApiResult<Void> result = apiNotificationFacade.markAllAsRead(principal);
    if (result.getStatus() == HttpStatus.BAD_REQUEST) {
      return ResponseEntity.badRequest().build();
    }
    return ResponseEntity.ok().build();
  }

  @GetMapping("/count")
  public ResponseEntity<Long> getUnreadCount(@AuthenticationPrincipal CustomUserDetails principal) {
    ApiResult<Long> result = apiNotificationFacade.getUnreadCount(principal);
    return ResponseEntity.ok(result.getResult());
  }
}
