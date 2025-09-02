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
  void hide_scale();
  void set_caption(QString caption);

private:
  Ui::ResultTab *ui;
};

#endif // RESULTTAB_HPP
