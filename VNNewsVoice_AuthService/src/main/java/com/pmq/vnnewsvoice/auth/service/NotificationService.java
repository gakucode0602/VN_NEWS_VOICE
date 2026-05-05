package com.pmq.vnnewsvoice.auth.service;

import com.pmq.vnnewsvoice.auth.pojo.Notification;
import java.util.List;

public interface NotificationService {
  Notification addNotification(Notification notification);

  Notification getNotificationById(Long id);

  Notification updateNotification(Notification notification);

  boolean deleteNotification(Long id);

  long countUnreadNotifications();

  List<Notification> getNotificationsByUserId(Long userId);

  List<Notification> getNotificationsByUserIdPaginated(Long userId, int page, int size);
}
