#ifndef RESULTTAB_HPP
#define RESULTTAB_HPP

#include <QWidget>

namespace Ui {
class ResultTab;
}

class ResultTab : public QWidget {
  Q_OBJECT

public:
  explicit ResultTab(QWidget *parent = nullptr);
  ~ResultTab();

  void set_preview(QPixmap image);
  uint get_preview_width();
  uint get_preview_height();
  void set_caption(QString caption);
  void hide_export_button(QString type);

private slots:
  void on_pb_refresh_clicked();
  void on_pb_export_index_clicked();
  void on_pb_export_text_clicked();

signals:
  void refresh_preview();
  void export_index();
  void export_text(QString);

private:
  Ui::ResultTab *ui;
};

#endif // RESULTTAB_HPP
