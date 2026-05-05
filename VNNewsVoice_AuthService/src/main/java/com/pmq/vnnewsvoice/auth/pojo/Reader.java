package com.pmq.vnnewsvoice.auth.pojo;

import jakarta.persistence.*;
import java.io.Serializable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "reader")
@Getter
@Setter
@NoArgsConstructor
public class Reader implements Serializable {

  private static final long serialVersionUID = 1L;

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  @Column(name = "id")
  private Long id;

  @JoinColumn(name = "user_id", referencedColumnName = "id")
  @OneToOne(optional = false)
  private UserInfo userId;

  public Reader(Long id) {
    this.id = id;
  }
}
