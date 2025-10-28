#include "importpage.hpp"
#include "ui_importpage.h"

ImportPage::ImportPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ImportPage) {
    ui->setupUi(this);
    page = PAGE::MAIN;
}

ImportPage::~ImportPage() {
    delete ui;
}

ImportPage::PAGE ImportPage::get_page() {
    return page;
}

void ImportPage::Landsat() {
    page = PAGE::CUSTOM_BANDS;
    ui->check_filenames_changed->hide();
    ui->verticalLayout->takeAt(2)->widget()->deleteLater();

    QWidget      *container = new QWidget(this);
    QGridLayout  *lyt = new QGridLayout();
    QHBoxLayout  *level_lyt = new QHBoxLayout();
    QLabel       *lb_level = new QLabel("Уровень обработки");
    QRadioButton *rb_l1 = new QRadioButton("Level 1");
    QRadioButton *rb_l2 = new QRadioButton("Level 2");
    rb_l1->toggle();
    QPushButton  *ok = new QPushButton("Ok");
    ok->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);

    level_lyt->addWidget(lb_level);
    level_lyt->addWidget(rb_l1);
    level_lyt->addWidget(rb_l2);
    lyt->addLayout(level_lyt, 0, 0, 1, 3);

    int rows = 12;
    for (int i = 1; i <= rows; i++) {
        QLabel      *lbl = new QLabel("Канал " + QString::number(i));
        QLineEdit   *le = new QLineEdit();
        QPushButton *pb = new QPushButton("Обзор");
        connect(pb, &QPushButton::clicked, [this, le, i, rows]() {
            if (i < rows) {
                QString f = QFileDialog::getOpenFileName(this,
                                                         "Открыть файл GeoTiff",
                                                         QDir::homePath(),
                                                         "GeoTiff (*.tif *.tiff *.TIF *.TIFF)");
                if (f.toLower().endsWith(".tif") || f.toLower().endsWith(".tiff")) {
                    le->setText(f);
                } else {
                    emit bad_band(f);
                }
            } else {
                QString f = QFileDialog::getOpenFileName(this, "Открыть файл MTL", QDir::homePath(), "Текст (*.txt)");
                if (f.toLower().endsWith(".txt")) {
                    le->setText(f);
                } else {
                    emit bad_metafile(f);
                }
            }
        });
        if (i == rows) {
            lbl->setText("Файл метаданных MTL");
        }
        lyt->addWidget(lbl, i, 0);
        lyt->addWidget(le, i, 1);
        lyt->addWidget(pb, i, 2);
    }

    connect(rb_l1, &QRadioButton::toggled, [lyt, rows](bool checked) {
        if (checked) {
            lyt->itemAtPosition(rows, 0)->widget()->show();
            lyt->itemAtPosition(rows, 1)->widget()->show();
            lyt->itemAtPosition(rows, 2)->widget()->show();
        } else {
            lyt->itemAtPosition(rows, 0)->widget()->hide();
            lyt->itemAtPosition(rows, 1)->widget()->hide();
            lyt->itemAtPosition(rows, 2)->widget()->hide();
        }
    });
    connect(ok, &QPushButton::clicked, [this, lyt, rb_l1, rows]() {
        QString                        proc_level, metafile;
        QList<QPair<QString, QString>> bands_files;
        for (int i = 1; i <= rows; i++) {
            QLabel    *lbl = qobject_cast<QLabel *>(lyt->itemAtPosition(i, 0)->widget());
            QLineEdit *le = qobject_cast<QLineEdit *>(lyt->itemAtPosition(i, 1)->widget());
            QString    band = lbl->text().split(' ').last();
            QString    file = le->text();
            if (file.toLower().endsWith(".tif") || file.toLower().endsWith(".tiff")) {
                bands_files.append(QPair<QString, QString>{band, file});
            }
            if (i == rows) {
                metafile = le->text();
            }
        }
        if (rb_l1->isChecked()) {
            proc_level = "L1TP";
        } else {
            proc_level = "L2SP";
        }
        emit custom_files(proc_level, metafile, bands_files);
    });

    lyt->addWidget(ok, rows + 1, 1);
    lyt->itemAtPosition(rows + 1, 1)->setAlignment(Qt::AlignHCenter);
    container->setLayout(lyt);
    ui->verticalLayout->insertWidget(2, container);
    emit custom_bands_page();
}

void ImportPage::to_satellite_select_page() {
    page = PAGE::MAIN;
    ui->verticalLayout->takeAt(2)->widget()->deleteLater();
    ui->check_filenames_changed->show();
    on_check_filenames_changed_checkStateChanged(Qt::Checked);
}

void ImportPage::on_check_filenames_changed_checkStateChanged(const Qt::CheckState &arg1) {
    if (arg1 == Qt::Checked) {
        QWidget     *container = new QWidget(this);
        QHBoxLayout *lyt = new QHBoxLayout();
        QPushButton *pb_Landsat = new QPushButton("Landsat 8/9");
        QPushButton *pb_Sentinel = new QPushButton("Sentinel 2");
        connect(pb_Landsat, &QPushButton::clicked, this, &ImportPage::Landsat);

        lyt->addWidget(pb_Landsat);
        lyt->addWidget(pb_Sentinel);
        container->setLayout(lyt);
        ui->verticalLayout->insertWidget(2, container);
        ui->pb_open_dir->hide();
        ui->pb_open_files->hide();
        emit satellite_select_page();
    } else {
        ui->verticalLayout->takeAt(2)->widget()->deleteLater();
        ui->pb_open_dir->show();
        ui->pb_open_files->show();
    }
}

void ImportPage::on_pb_open_dir_clicked() {
    QDir dir = QFileDialog::getExistingDirectory(this, "Открыть директорию", QDir::homePath());
    emit directory(dir);
}

void ImportPage::on_pb_open_files_clicked() {
    QStringList filenames = QFileDialog::getOpenFileNames(this,
                                                          "Открыть файлы",
                                                          QDir::homePath(),
                                                          "GeoTiff, Text (*.tif *.tiff *.TIF *.TIFF *.txt)");
    emit files(filenames);
}
