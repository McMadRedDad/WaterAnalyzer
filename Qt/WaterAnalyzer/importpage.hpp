#ifndef IMPORTPAGE_HPP
#define IMPORTPAGE_HPP

#include <QDir>
#include <QFileDialog>
#include <QLabel>
#include <QLineEdit>
#include <QWidget>

namespace Ui {
class ImportPage;
}

class ImportPage : public QWidget {
  Q_OBJECT

public:
  enum PAGE { MAIN, CUSTOM_BANDS };

  explicit ImportPage(QWidget *parent = nullptr);
  ~ImportPage();

  PAGE get_page();

public slots:
  void to_satellite_select_page();

private slots:
  void Landsat();
  void on_check_filenames_changed_checkStateChanged(const Qt::CheckState &arg1);
  void on_pb_open_dir_clicked();
  void on_pb_open_files_clicked();

signals:
  void custom_bands_page();
  void satellite_select_page();
  void bad_band(QString);
  void custom_files(QList<QPair<QString, QString>>);
  void directory(QDir);
  void files(QStringList);

private:
  Ui::ImportPage *ui;
  PAGE page;
};

#endif // IMPORTPAGE_HPP
