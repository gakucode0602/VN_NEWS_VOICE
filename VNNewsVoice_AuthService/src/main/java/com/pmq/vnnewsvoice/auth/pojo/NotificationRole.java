package com.pmq.vnnewsvoice.auth.pojo;

import jakarta.persistence.*;
import java.io.Serializable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "notificationrole")
@Getter
@Setter
@NoArgsConstructor
public class NotificationRole implements Serializable {

  private static final long serialVersionUID = 1L;

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @JoinColumn(name = "notification_id", referencedColumnName = "id")
  @ManyToOne(optional = false)
  private Notification notificationId;

  @JoinColumn(name = "role_id", referencedColumnName = "id")
  @ManyToOne(optional = false)
  private Role roleId;

  public NotificationRole(Long id) {
    this.id = id;
  }
}
