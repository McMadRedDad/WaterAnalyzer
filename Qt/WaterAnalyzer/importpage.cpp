#include "importpage.hpp"
#include "ui_importpage.h"

ImportPage::ImportPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ImportPage) {
  ui->setupUi(this);
}

ImportPage::~ImportPage() { delete ui; }

void ImportPage::on_check_filenames_changed_checkStateChanged(
    const Qt::CheckState &arg1) {
  if (arg1 == Qt::Checked) {
    QHBoxLayout *lyt = new QHBoxLayout();
    QPushButton *pb_Landsat = new QPushButton("Landsat 8/9");
    QPushButton *pb_Sentinel = new QPushButton("Sentinel 2");
    lyt->addWidget(pb_Landsat);
    lyt->addWidget(pb_Sentinel);
    ui->verticalLayout->insertLayout(2, lyt);
    ui->pb_open_dir->hide();
    ui->pb_open_files->hide();
  } else {
    // delete/hide lyt
    ui->pb_open_dir->show();
    ui->pb_open_files->show();
  }
}

void ImportPage::on_pb_open_dir_clicked() {
  QDir dir = QFileDialog::getExistingDirectory(this, "Открыть директорию",
                                               QDir::homePath());
  emit directory(dir);
}

void ImportPage::on_pb_open_files_clicked() {
  QStringList filenames =
      QFileDialog::getOpenFileNames(this, "Открыть файлы", QDir::homePath(),
                                    "GeoTiff (*.tif *.tiff *.TIF *.TIFF)");
  emit files(filenames);
}
