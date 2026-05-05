package com.pmq.vnnewsvoice.auth.facade.impl;

import com.pmq.vnnewsvoice.auth.dto.ApiResult;
import com.pmq.vnnewsvoice.auth.dto.NotificationDto;
import com.pmq.vnnewsvoice.auth.facade.ApiNotificationFacade;
import com.pmq.vnnewsvoice.auth.mapper.NotificationMapper;
import com.pmq.vnnewsvoice.auth.pojo.CustomUserDetails;
import com.pmq.vnnewsvoice.auth.pojo.Notification;
import com.pmq.vnnewsvoice.auth.service.NotificationService;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ApiNotificationFacadeImpl implements ApiNotificationFacade {
  private final NotificationService notificationService;
  private final NotificationMapper notificationMapper;

  @Override
  public ApiResult<NotificationDto> markAsRead(Long id, CustomUserDetails principal) {
    Optional<Notification> notificationOpt =
        Optional.ofNullable(notificationService.getNotificationById(id));
    if (notificationOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy thông báo");
    }

    Notification notification = notificationOpt.get();
    if (!notification.getUserId().getId().equals(principal.getUserInfo().getId())) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy thông báo");
    }

    notification.setIsRead(true);
    Notification updated = notificationService.updateNotification(notification);
    NotificationDto notificationDto = notificationMapper.toDto(updated);
    return ApiResult.success(HttpStatus.OK, notificationDto);
  }

  @Override
  public ApiResult<Void> markAllAsRead(CustomUserDetails principal) {
    if (principal == null) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Không hợp lệ");
    }

    Long userId = principal.getUserInfo().getId();
    List<Notification> notifications = notificationService.getNotificationsByUserId(userId);

    for (Notification notification : notifications) {
      if (!notification.getIsRead()) {
        notification.setIsRead(true);
        notificationService.updateNotification(notification);
      }
    }

    return ApiResult.success(HttpStatus.OK, null);
  }

  @Override
  public ApiResult<Long> getUnreadCount(CustomUserDetails principal) {
    if (principal == null) {
      return ApiResult.success(HttpStatus.OK, 0L);
    }
    long count = notificationService.countUnreadNotifications();
    return ApiResult.success(HttpStatus.OK, count);
  }
}
